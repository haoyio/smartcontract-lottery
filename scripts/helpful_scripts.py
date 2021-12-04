from brownie import (
    Contract,
    LinkToken,
    MockV3Aggregator,
    VRFCoordinatorMock,
    accounts,
    interface,
    network,
    config,
)


FORKED_LOCAL_ENVIRONMENTS = ["mainnet-fork", "mainnet-fork-dev"]
LOCAL_BLOCKCHAIN_ENVIRONMENTS = ["development", "ganache-local"]

DECIMALS = 8
INITIAL_VALUE = 200000000000


def get_account(index=None, id=None):
    # accounts[0]: brownie ganache account
    # accounts.add("env"): environment variables
    # accounts.load("id")
    if index:
        return accounts[index]

    if id:
        return accounts.load(id)

    # local blockchain
    if (
        network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS
        or network.show_active() in FORKED_LOCAL_ENVIRONMENTS
    ):
        return accounts[0]

    # default
    return accounts.add(config["wallets"]["from_key"])


contract_to_mock = {
    "eth_usd_price_feed": MockV3Aggregator,
    "vrf_coordinator": VRFCoordinatorMock,
    "link_token": LinkToken,
}


def get_contract(contract_name):
    """This function will grab the contract addresses from the brownie config
    if defined, otherwise, it will deploy a mock version of that contract, and
    return that mock contract.

    Args:
        contract_name (string)

    Returns:
        brownie.network.contract.ProjectContract: the most recently deployed
            version of this contract
    """
    contract_type = contract_to_mock[contract_name]
    if network.show_active() in LOCAL_BLOCKCHAIN_ENVIRONMENTS:
        if len(contract_type) <= 0:
            # MockV3Aggregator.length
            deploy_mocks()
        contract = contract_type[-1]  # most recent contract
        # MockV3Aggregator[-1]

    else:
        contract_address = config["networks"][network.show_active()][contract_name]
        # address
        # ABI
        contract = Contract.from_abi(
            contract_type._name, contract_address, contract_type.abi
        )
        # MockV3Aggregator.abi

    return contract


def deploy_mocks(decimals=DECIMALS, initial_value=INITIAL_VALUE):
    account = get_account()
    link_token = LinkToken.deploy({"from": account})
    MockV3Aggregator.deploy(decimals, initial_value, {"from": account})
    VRFCoordinatorMock.deploy(link_token.address, {"from": account})
    print("Deployed!")


def fund_with_link(
    contract_address,
    account=None,
    link_token=None,
    amount=100000000000000000,  # 0.1 LINK
):
    account = account if account is not None else get_account()
    link_token = link_token if link_token is not None else get_contract("link_token")
    tx = link_token.transfer(contract_address, amount, {"from": account})

    # can use an interface instead of above, which may be unwieldy because if you want
    # to interact with it in other ways you need the address, abi to get the contract
    # i.e., something like
    # contract = Contract.from_abi(
    #     contract_type._name, contract_address, contract_type.abi
    # )
    # whereas with an interface brownie can just figure out how to interact with the
    # contract and grab the abi by itself(?)
    # link_token_contract = interface.LinkTokenInterface(link_token.address)
    # tx = link_token_contract.transfer(contract_address, amount, {"from": account})

    tx.wait(1)
    print("Funded contract!")
    return tx
