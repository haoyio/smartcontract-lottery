import time
from brownie import Lottery, config, network
from scripts.helpful_scripts import fund_with_link, get_account, get_contract


def deploy_lottery():
    account = get_account()
    lottery = Lottery.deploy(
        get_contract("eth_usd_price_feed").address,
        get_contract("vrf_coordinator").address,
        get_contract("link_token").address,
        config["networks"][network.show_active()]["fee"],
        config["networks"][network.show_active()]["keyhash"],
        {"from": account},
        # to publish source code to the chain; e.g., Rinkeby
        publish_source=config["networks"][network.show_active()].get("verify", False),
    )
    print("Deployed lottery!")
    return lottery


def start_lottery():
    account = get_account()
    lottery = Lottery[-1]
    starting_tx = lottery.startLottery({"from": account})
    starting_tx.wait(1)  # [second] brownie sometimes get confused if you don't wait(?)
    print("The lottery is started!")


def enter_lottery():
    account = get_account()
    lottery = Lottery[-1]
    value = (
        lottery.getEntranceFee() + 10000000
    )  # tack on a little bit of wei for rounding(?)
    tx = lottery.enter({"from": account, "value": value})
    tx.wait(1)
    print("You entered the lottery!")


def end_lottery():
    account = get_account()
    lottery = Lottery[-1]
    # need to fund contract first to request randomness and then end the lottery
    tx = fund_with_link(lottery.address)
    tx.wait(1)
    ending_tx = lottery.endLottery({"from": account})
    ending_tx.wait(1)
    print(f"expected winning account = {lottery.players(0)} (because only account)")

    n_minutes_waited = 0
    while lottery.lottery_state() == 2 and n_minutes_waited < 10:  # calculating winner
        time.sleep(60)  # sleep for 1 min
        print(f"lottery_state = {lottery.lottery_state()}")
        n_minutes_waited += 1

    if lottery.lottery_state() == 2:  # calculating winner
        print(f"Timed out waiting for fulfillRandomness...")
    else:
        print(f"{lottery.recentWinner()} is the new winner!")
    # problem here is going to be that no one is calling fulfillRandomness in unit test,
    # which means we won't have a winner (defaults to 0x0); need to sidestep in unit test


def main():
    deploy_lottery()
    start_lottery()
    enter_lottery()
    end_lottery()
