# Fetch

``` python
from ccgp import fetch_ccgp_bid_info
fetch_ccgp_bid_info('name.json', how_many_pages)
```

Bid info will be stored in `name.txt`. Web pages will be stored in the
folder `name/`.

# Analyze

``` python
from analyze import analyze_money
analyze_money('name.json')
```

Read from `name.json` and analyze money in each web page.
