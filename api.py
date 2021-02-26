import constants
import uvicorn
from fastapi import FastAPI
from fastapi import HTTPException
from fastapi.openapi.utils import get_openapi
from fastapi.openapi.docs import get_redoc_html
from fastapi import Query

import models


class UnicornException(Exception):
    def __init__(self, name: str):
        self.name = name


app = FastAPI()

@app.get("/", include_in_schema=False)
def overridden_redoc():
    return get_redoc_html(openapi_url="/openapi.json", title="Cast-MyVote API",
                          redoc_favicon_url="https://i.imgur.com/5X2efLp.png")


def custom_openapi():
    if app.openapi_schema:
        return app.openapi_schema
    openapi_schema = get_openapi(
        title="Cast-MyVote API",
        version="v1.0.0",
        description="A REST API to create Polls, cast votes on Polls, fetch Poll details, results.\n"
                    "Built on top of Blockchain to providing full decentralization"
                    "<h1>✨ Features</h1>"
                    "<ul><li> 🗳️ &nbsp;&nbsp;Create polls with as many options you "
                    "want, also set a name and limit for your "
                    "poll.</li> "
                    "<li> ⏲ &nbsp;&nbsp;Poll vote counting stops automatically when total no. of votes hits the poll limit.</li>"
                    "<li> 📇 &nbsp;&nbsp;&nbsp;Fetch poll details</li>"
                    "<li> 📥 &nbsp;&nbsp;Cast votes on a particular poll</li>"
                    "<li> ⏲ &nbsp;&nbsp;Get live count of votes on a poll</li>"
                    "<li> ▶️  &nbsp;&nbsp;Check if a poll is still active or not</li>"
                    "<li> 📉 &nbsp;&nbsp;Get final results of a poll</li></ul>",
        routes=app.routes,
    )
    openapi_schema["info"]["x-logo"] = {
        "url": "https://i.imgur.com/Abg3WeV.png"
    }
    app.openapi_schema = openapi_schema
    return app.openapi_schema


app.openapi = custom_openapi


@app.post("/api/poll/new",
          response_model=models.NewPollOutput,
          tags=["🗳️ Create Poll"],
          summary="This endpoint is used to create a new poll",
          response_description="Returns newly created poll id i.e new contract in Blockchain to hold the Poll data"
          )
def create_poll(poll: models.NewPollInput):
    """
       Creates a new poll with this properties ➡️
       - **name**: each poll created must have a name
       - **options**: list of options for the poll
       - **limit**: each poll must have a max voting limit
     """
    try:
        options = []
        for item in poll.options:
            x = item
            x = bytes(x, 'utf-8')
            options.append(x)

        VotingContract = constants.init_contract()
        tx = VotingContract.constructor(options, poll.name, poll.limit) \
            .buildTransaction(
            {'nonce': constants.web3.eth.getTransactionCount(
                constants.web3.toChecksumAddress(constants.wallet_address)
            )}
        )

        signed_tx = constants.web3.eth.account.signTransaction(tx, private_key=constants.private_key)
        tx_hash = constants.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        tx_receipt = constants.web3.eth.waitForTransactionReceipt(tx_hash.hex())

        return {"id": tx_receipt.contractAddress}

    except Exception as error:
        raise HTTPException(status_code=418, detail=str(error))


@app.get("/api/poll",
         response_model=models.PollDetails,
         tags=["📇 Fetch Poll Info"],
         summary="This endpoint is used to fetch details of a poll",
         response_description="Returns Poll data associated with the supplied poll id",

         )
def get_poll_details(id: str = Query(None, description='Id of the poll whose detail needs to fetched')):
    """
       Fetches a ongoing poll info having these following detail ➡️
       - **name**: name of the poll
       - **options**: list of options for the poll
       - **limit**: max votes allowed for the poll
       - **count**: total number of votes casted in the pol
    """
    try:
        contract = constants.get_contract(id)
        poll_details = contract.functions.getVotingDetails().call()

        poll_option_list = list(poll_details[0].split(","))  # contains the option list
        poll_option_list = poll_option_list[:-1]

        return {"options": poll_option_list,
                "name": poll_details[1],
                "limit": poll_details[2],
                "count": poll_details[3]
                }
    except Exception as error:
        raise HTTPException(status_code=418, detail=str(error))


@app.get("/api/poll/livedata",
         response_model=models.PollLiveCount,
         tags=["⏲ Fetch Poll Live count"],
         summary="This endpoint is used to fetch the live count of a poll"
         )
def get_live_count(id: str= Query(None, description='id of the poll whose live count needs to fetched')):

    try:
        contract = constants.get_contract(id)
        poll_option_list = contract.functions.getOptionList().call()
        poll_live_count = contract.functions.getLiveCount().call()
        poll_option_list = list(poll_option_list[:-1].split(","))

        live_count = {}
        for i in range(0, len(poll_option_list)):
            live_count[poll_option_list[i]] = poll_live_count[i]

        return {"livedata": live_count}

    except Exception as err:
        raise HTTPException(status_code=418, detail=str(err))


@app.post("/api/poll",
          response_model=models.StatusOutput,
          tags=["📥 Cast vote on a Poll"],
          summary="This endpoint is used to cast a vote on a particular poll",
          response_description="If casting of vote is successful than it return true else it returns false"
          )
def cast_vote(vote: models.CastVoteInput, id: str=Query(None, description='id of the poll on which vote will be casted')):

    try:
        contract = constants.get_contract(id)
        tx = contract.functions.castVote(vote.option, vote.id) \
            .buildTransaction(
            {'nonce': constants.web3.eth.getTransactionCount(
                constants.web3.toChecksumAddress(constants.wallet_address))}
        )

        signed_tx = constants.web3.eth.account.signTransaction(tx, private_key=constants.private_key)
        tx_hash = constants.web3.eth.sendRawTransaction(signed_tx.rawTransaction)
        constants.web3.eth.waitForTransactionReceipt(tx_hash.hex())
        is_vote_successful = contract.functions.hasUserVoted().call()

        return {"status": is_vote_successful}

    except Exception as error:
        raise HTTPException(status_code=418, detail=str(error))


@app.get("/api/poll/status",
         response_model=models.StatusOutput,
         tags=["▶️ Get Poll status"],
         summary="This endpoint is to check completion status of a poll",
         response_description="Returns true if Poll is over else returns false")
def get_poll_status(id: str = Query(None, description='id of the poll whose status needs to be fetched')):
    """
        Checks if a particular Poll is over or not
    """
    try:
        contract = constants.get_contract(id)
        status = contract.functions.getPollStatus().call()
        return {"status": status}
    except Exception as error:
        raise HTTPException(status_code=418, detail=str(error))


@app.get("/api/poll/result",
         response_model=models.PollResult,
         tags=["📉 Get Poll result"],
         summary="This endpoint is used to get the final result of a Poll",
         )
def get_poll_result(id: str= Query(None, description='id of the poll whose result needs to be fetched')):
    try:
        contract = constants.get_contract(id)
        result = contract.functions.getPollResult().call()
        vote_count = result[1]
        # if poll is still going on than return empty dict
        if vote_count == 0:
            return {"result": {}}

        return {"result": {result[0]: vote_count}}

    except Exception as error:
        raise HTTPException(status_code=418, detail=str(error))


if __name__ == "__main__":
    uvicorn.run(app, host="192.168.31.164", port=8000)
