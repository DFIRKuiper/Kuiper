# Convert SIGMA rules to Rhaegal rules

You can use the script called `SigmaToRhaegal.py` in this repository to convert SIGMA rules to Rhaegal rules. Keep in mind that the script is still in the `alpha`  version there is a lot of rules you have to double check if the script converted the rule correctly. 

# Command Line & Help Message

Here is the help message of the script:

```
usage: SigmaToRhaegal.py [-h] -r RULESDIR -o OUTPUT

Convert SIGMA rules to Rhaegal rules

optional arguments:
  -h, --help            show this help message and exit
  -r RULESDIR, --rulesDir RULESDIR
                        Path that contains SIGMA rules.
  -o OUTPUT, --output OUTPUT
                        The path where the results will be saved.
```

you can use the script  like this:

`python3 SigmaToRhaegal.py -r ./SIGMARules/ -o ./SIGMAToRhaegal.gh` 