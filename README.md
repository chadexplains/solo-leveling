## setup
1. virtualenv env
2. env/bin/activate
3. create a file `.env` and `token.json` one level up from where this `README.md` file is and fill it with the required secrets
2. run
```
make setup
```


## run the discord bot
```
make discord_bot
```

this automatically installs python dependencies


## start work on a new feature
```
make feature
```


## committing changes
```
make push
```

this automatically formats the code, then commits and pushes


## releasing a feature
```
make release
```

this automatically pushes and creates a pull request with its title set to the feature name


## ssh into AWS box
```
ssh ubuntu@ec2-3-83-214-95.compute-1.amazonaws.com  -i ~/Downloads/discord.pem
cd /home/ec2-user/app
```


## links
* airtable: https://airtable.com/app8xDpApplv8WrVJ/tblq9OP7XbjDidPZC/viwuD5OT73LN5yaEg?blocks=hide
* discord: https://discord.gg/Qbm4mgSr
