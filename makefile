there_is_no_default_target:
	@echo "there is no default target, look at the makefile to see what targets you can build"
	@exit 1


###### project setup and building ######


setup: ../.env
	python3 -m pip install poetry
	python3 -m pip install black
	python3 -m pip install isort
	python3 -m pip install flake8
	if [[ ! -f ".env" ]]; then \
	  ln ../.env ./.env; \
	fi
	if [[ ! -f "token.json" ]]; then \
	  ln ../token.json ./token.json; \
	fi

format:
	isort .
	black --line-length 100 .
	flake8 --max-line-length=300 --ignore=E203,W503 .

test: format test_*.py
	python3 -m poetry run python3 -m unittest test_*.py

build: pyproject.toml
	python3 -m poetry lock --no-update
	python3 -m poetry install

clean: __pycache__ poetry.lock
	rm -rf __pycache__
	rm poetry.lock


###### run apps ######


discord_bot: build discord_bot.py
	python3 -m poetry run python3 discord_bot.py

upload_leetcode_questions_to_airtable: build upload_leetcode_questions_to_airtable.py
	python3 -m poetry run python3 upload_leetcode_questions_to_airtable.py


###### git helpers ######


feature:
	@read -p "feature name (eg make-bot-do-thing): " feature_name; \
	\
	git checkout main; \
	git pull; \
	\
	git checkout -b $${feature_name}; \
	git push --set-upstream origin $${feature_name}

push: format
	git add .
	git commit -am "_" --allow-empty
	git push

release: build push
	gh pr create --base main --title "$(shell git branch --show-current)" --body "_"
