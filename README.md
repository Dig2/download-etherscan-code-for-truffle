# download-etherscan-code-for-truffle
Download solidity source code from etherscan verified smart contract via inputing address or url

## why

Copying code snippets from etherscan's code page into the workspace is a hassle, so I wrote this little tool.

## How

Fill in your etherscan api key in config.py

add `alias c='python3 path/to/index.py` to `~/.bashrc`

then

```shell
c https://etherscan.io/address/0x025C6da5BD0e6A5dd1350fda9e3B6a614B205a1F
// or
c 0x025C6da5BD0e6A5dd1350fda9e3B6a614B205a1F
```

It will download solidity source file and save it to `./contracts/<contract_name>/<files>`