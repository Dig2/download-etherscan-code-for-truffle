#! /usr/bin/python3
from config import *
import sys, re, requests, json, os, shutil


def import_replace(matched):
    return "import \"./" + os.path.basename(matched.group('filename')) + "\"";


def pre_check():
    global contract_address
    global chain_id
    
    chain_id = ChainId.ETHEREUM  # default Ethereum
    for i, j in BROWSER_URL.items():
        if j in sys.argv[1]:
            chain_id = i
    print("Chain id:", bcolors.OKGREEN, chain_id, bcolors.ENDC)

    if (len(sys.argv) != 2):
        sys.exit(bcolors.FAIL + "Usage: need exactly 2 parameters, <URL>" + bcolors.ENDC)

    res = re.findall(r'.*([0-9a-zA-Z]{40}).*', sys.argv[1])

    if (len(res) != 1):
        sys.exit(bcolors.FAIL + "Confused about given URL or address" + bcolors.ENDC)

    contract_address = "0x" + res[0]


def real_res():
    global contract_address
    global chain_id

    while True:
        print( "Searching solidity code of address:", bcolors.OKGREEN , contract_address, bcolors.ENDC)
        res = requests.get(RPC_ENDPOINTS['getsourcecode'].format(BROWSER_URL[chain_id], contract_address, API_KEY[chain_id])).json()
        contract_name = res['result'][0]['ContractName']

        if contract_name == 'Diamond':
            sys.exit(bcolors.FAIL + f"Diamond proxy contract pattern: https://{BROWSER_URL[chain_id]}/address/{contract_address}#code. Please check it manually." + bcolors.ENDC)
        
        if contract_name in ['UpgradeableProxy', 'TransparentUpgradeableProxy', 'AdminUpgradeabilityProxy', 'BeaconProxy']:
            c = input(f"This contract seems like a proxy contract, {bcolors.WARNING}find its implementation{bcolors.ENDC} or not?({bcolors.WARNING}Y{bcolors.ENDC}/n)")
            if c != 'n':
                slot = "0xa3f0ad74e5423aebfd80d3ef4346578335a9a72aeaee59ff6cb3582b35133d50" if contract_name in ['BeaconProxy'] else "0x360894a13ba1a3210667c828492db98dca3e2076cc3735a920a3ca505d382bbc"
                payload = {"jsonrpc":"2.0", "method": "eth_getStorageAt", "params": [contract_address, slot, "latest"], "id": 1}
                logic_address = "0x" + requests.post(RPC_URL[chain_id], json = payload).json()['result'][-40:]
                contract_address = logic_address
                print( "Found logic contract address:", bcolors.OKGREEN , contract_address, bcolors.ENDC)
                if contract_name in ['BeaconProxy']:
                    sys.exit(bcolors.FAIL + f"Beacon proxy contract pattern: https://{BROWSER_URL[chain_id]}/address/{contract_address}#code. Please check it manually." + bcolors.ENDC)
                continue
        break

    return res


def create_directory(directory):
    print("Creating directory:", bcolors.OKBLUE, directory, bcolors.ENDC)
    while os.path.exists(directory):
        c = input(f"source file direct already exists, replace it, save as another name or {bcolors.WARNING}cancel{bcolors.ENDC}?(r/s/{bcolors.WARNING}C{bcolors.ENDC})")
        if c == 'r':
            shutil.rmtree(directory)
        elif c == 's':
            directory = directory + "_1"
            print("Creating directory:", bcolors.OKBLUE, directory, bcolors.ENDC)
        else:
            sys.exit(bcolors.FAIL + "cancel" + bcolors.ENDC)
    os.makedirs(directory)


def write_files(codes, contract_name, base_dir):
    if (codes[0] == '{'):
        if codes[1] == '{':
            codes = json.loads(codes[1:-1])['sources']
        else:
            codes = json.loads(codes)

        for i in codes:
            raw_code = codes[i]['content']
            data = re.sub(r".*import.*['\"](?P<filename>.*\.sol)['\"]", import_replace, raw_code)

            filename = os.path.join(base_dir, os.path.basename(i))
            print("Writing file:", bcolors.OKBLUE, filename, bcolors.ENDC)
            with open(filename, "w") as f:
                f.write(data)
    else:
        each_files = re.findall(r"\/\/ File ([\s\S]*?\.sol)(?:.*)([\s\S]*?)(?=\/\/ File|$)", codes)
        each_parts = re.findall(r"pragma\s+solidity([\s\S]*?)(?=\/\/ File|$)", codes)


        if len(each_files) != len(each_parts):
            print(bcolors.FAIL + "Something error, writing as single file" + bcolors.ENDC)
        if len(each_files) == 0 or len(each_files) != len(each_parts):
            full_filename = os.path.join(base_dir, contract_name+".sol")
            print("Writing file:", bcolors.OKBLUE, full_filename, bcolors.ENDC)
            with open(full_filename, "w") as f:
                f.write(codes)
            return

        last_file = ""
        for (filename, code) in each_files:
            full_filename = os.path.join(base_dir, os.path.basename(filename))
            print("Writing file:", bcolors.OKBLUE, full_filename, bcolors.ENDC)
            with open(full_filename, "w") as f:
                f.write((f"import \"./{last_file}\";\r\n" if last_file else "") + code.strip("\r\n"))

            last_file = os.path.basename(filename)


def work():

    res = real_res()

    contract_name = res['result'][0]['ContractName']
    codes = res['result'][0]['SourceCode']
    base_dir = os.path.join(os.getcwd(), "contracts", contract_name)

    create_directory(base_dir)  # create directory: ./contracts/{contract name}
    write_files(codes, contract_name, base_dir)
    
        
def main():
    pre_check()
    work()


if __name__ == "__main__":
    main()
