import json
from pydantic import BaseModel, Field


class NewPollInput(BaseModel):
    name: str = Field(...,description="Name of the poll", example="Random Poll name")
    options: list = Field(...,description="List of options for the poll", example=["Option A", "Option B", "Option C"])
    limit: int = Field(...,description="Max no. of votes allowed for the poll", example=150)


class CastVoteInput(BaseModel):
    id: int = Field(...,description="Unique id to identify a user who is casting vote", example=1876363583)
    option: str = Field(...,description="The option on which user is casting vote", example="Option 1")


class NewPollOutput(BaseModel):
    id: str= Field(...,description="Id of a newly created poll",
                   example="0xb5b5FF0987067f166169f082c174402277954f35")




class PollDetails(BaseModel):
    name: str = Field(...,description="Name of the poll", example="Poll name")
    options: list = Field(...,description="Options of the poll", example=["Option A", "Option B", "Option C"])
    limit: int = Field(...,description="Max vote limit of the poll", example=150)
    count: int = Field(...,description="No. of votes casted on the poll", example=100)


class PollLiveCount(BaseModel):
    livedata: dict = Field(...,description="Contains vote count of each options of the poll",
                           example={"Option A": 13, "Option B": 18})


class PollResult(BaseModel):
    result: dict = Field(...,description="Contains winning option and its vote count",
                             example={"Option B": 17})


class StatusOutput(BaseModel):
    status: bool = Field(...,description="Boolean value to indicate various event status\n"
                                         "returns true in case \n"
                                         "1. A vote got casted successfully\n"
                                         "2. An ongoing poll is over i.e not accepting votes anymore", example="true")
