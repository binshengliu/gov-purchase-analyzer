# Government Bidding Analyzer

Fetch bidding information from government website and analyze amount
of money.

## Fetch Bidding Data

``` python
from ccgp import fetch_ccgp_bid_info, BidType
fetch_ccgp_bid_info('keyword', how_many_pages, 
                    'name.json',  type=BidType.CALL_FOR_BIDDING,
                    start='2018-01-01', end='2018-01-31')
```

Bid types:

```
BidType.ALL
BidType.CALL_FOR_BIDDING
BidType.SUCCESSFUL_BIDDING
BidType.DEAL

```

Bid info will be stored in `name.json`. Web pages will be stored in
the folder `name/`.

## Analyze Amount of Money

``` python
from analyze import analyze_money
analyze_money('name.json')
```

Read from `name.json` and analyze money in each web page.
