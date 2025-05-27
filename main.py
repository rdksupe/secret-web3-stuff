import requests
import pandas as pd
from datetime import datetime
from collections import Counter
import json
from llm_utils import summarize_profile, generate_handle, analyze_entities

# new helper to recursively remove hex strings
def clean_args(arg):
    if isinstance(arg, list):
        cleaned = []
        for x in arg:
            c = clean_args(x)
            if c is None: continue
            if isinstance(c, list) and not c:  # drop empty lists
                continue
            cleaned.append(c)
        return cleaned
    if isinstance(arg, str):
        return None if arg.startswith("0x") else arg
    return arg

def get_wallet_transactions(wallet_address, limit=100):
    url = f"https://fullnode.mainnet.aptoslabs.com/v1/accounts/{wallet_address}/transactions?limit={limit}"
    
    response = requests.get(url)
    if response.status_code != 200:
        raise Exception(f"API request failed with status {response.status_code}: {response.text}")
    
    transactions = response.json()
    formatted_txs = []
    
    for tx in transactions:
        # print full payload for each transaction
        
        version = tx.get('version')
        tx_type = tx.get('type')
        timestamp = datetime.fromtimestamp(int(tx.get('timestamp')) / 1000000).isoformat()
        sender = tx.get('sender')
        
        # Extract payload information
        sent_to = ''
        function_name = ''
        amount = ''
        payload_args = []                   # new: init args list

        if tx_type == 'user_transaction' and tx.get('payload', {}).get('type') == 'entry_function_payload':
            payload = tx.get('payload', {})
            # pull out only the function name (last segment after ::)
            full_fn = payload.get('function', '')
            # drop the address prefix, keep "Module::function"
            function_name = "::".join(full_fn.split("::")[1:]) if full_fn else ''
            raw_args = payload.get('arguments', [])
            # apply cleaning
            payload_args = clean_args(raw_args)

            # Try to extract recipient and amount for common transfer functions
            if 'transfer' in function_name:
                if len(payload_args) >= 1:
                    sent_to = payload_args[0]
                if len(payload_args) >= 2:
                    amount = payload_args[1]
        
        formatted_txs.append({
            'Version': version,
            'Type': tx_type,
            'Timestamp': timestamp,
            'Sender': sender,
            'Sent To': sent_to,
            'Function': function_name,
            'Amount': amount,
            'Arguments': payload_args        # new: include full args
        })
    
    return formatted_txs

def main():
    wallet_address = "0xc6318f3c6f47d048ec9b1440025e16dbbe71d2713b11ccd7d22464368e5932f7"
    print(wallet_address)  # Replace with actual address
    transactions = get_wallet_transactions(wallet_address)
    if not transactions:
        print("No transactions found for this wallet.")
        return
    
    # fetch on‐chain resources for balances
    res_url = f"https://fullnode.mainnet.aptoslabs.com/v1/accounts/{wallet_address}/resources"
    resources = requests.get(res_url).json()
    coin_balances = []
    for resource in resources:
        t = resource.get("type","")
        if t.startswith("0x1::coin::CoinStore<"):
            coin_type = t.split("<",1)[1].rstrip(">")
            symbol = coin_type.split("::")[-1]
            bal = resource.get("data",{}).get("coin",{}).get("value","0")
            coin_balances.append({"symbol":symbol,"balance":bal})

    # count transaction categories
    tx_types = Counter()
    for tx in transactions:
        if tx["Type"]=="user_transaction":
            fn = tx.get("Function","")
            if "transfer" in fn:      tx_types["Transfer"]+=1
            elif "swap" in fn:         tx_types["Swap"]+=1
            elif any(x in fn for x in ("pool","lend","borrow")): tx_types["DeFi"]+=1
            elif "nft" in fn.lower():  tx_types["NFT"]+=1
            else:                      tx_types["Other"]+=1

    tx_count = len(transactions)
    primary_activity = tx_types.most_common(1)[0][0] if tx_types else "None"

    # wallet age in days
    if transactions:
        # convert ISO strings back to timestamps
        ts_list = [
            datetime.fromisoformat(tx["Timestamp"]).timestamp()
            for tx in transactions
        ]
        first_ts = min(ts_list)
        age_days = (datetime.now().timestamp() - first_ts) / 86400
    else:
        age_days = 0

    # persona rules
    persona="Unclassified"
    if tx_count==0:
        persona="Inactive"
    elif tx_types.get("DeFi",0) > tx_count*0.3:
        persona="Active DeFi User"
    elif tx_count>50:
        persona="Active Trader"
    elif len(coin_balances)>5:
        persona="Diversified Investor"
    elif tx_types.get("NFT",0) > tx_count*0.3:
        persona="NFT Collector"
    elif age_days>30 and tx_count<10:
        persona="Long-term Holder"

    # assemble profile
    profile = {
        "address": wallet_address,
        "wallet_age_days": int(age_days),
        "total_transactions": tx_count,
        "primary_activity": primary_activity,
        "persona": persona,
        "coin_balances": coin_balances,
        "tx_type_counts": dict(tx_types)
    }
    # count and record top functions
    func_counter = Counter(tx.get("Function","") for tx in transactions)
    profile["top_functions"] = [
        {"name": fn, "count": ct}
        for fn, ct in func_counter.most_common()
    ]

    # call LLM for health summary and handle
    profile["health_summary"]   = summarize_profile(profile)
    profile["social_handle"]    = generate_handle(profile)
    profile["entity_insights"]  = analyze_entities(transactions)

    # persist and display
    with open("wallet_profile.json","w") as f:
        json.dump(profile, f, indent=2)
    print("Enhanced profile:", json.dumps(profile, indent=2))

if __name__ == "__main__":
    main()