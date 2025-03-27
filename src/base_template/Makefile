install:
	@command -v uv >/dev/null 2>&1 || { echo "uv is not installed. Installing uv..."; curl -LsSf https://astral.sh/uv/install.sh | sh; source ~/.bashrc; }
	uv sync --dev {% if cookiecutter.agent_name != 'multimodal_live_api' %}--extra streamlit{%- endif %} --extra jupyter --frozen{% if cookiecutter.agent_name == 'multimodal_live_api' %} && npm --prefix frontend install{%- endif %}

test:
	uv run pytest tests/unit && uv run pytest tests/integration

playground:
{%- if cookiecutter.deployment_target == 'cloud_run' %}
	uv run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload &
{%- endif %}
{%- if cookiecutter.agent_name == 'multimodal_live_api' %}
	npm --prefix frontend start
{%- else %}
	{% if cookiecutter.deployment_target == 'agent_engine' %}PYTHONPATH=. {% endif %}uv run streamlit run frontend/streamlit_app.py --browser.serverAddress=localhost --server.enableCORS=false --server.enableXsrfProtection=false
{%- endif %}

backend:
{%- if cookiecutter.deployment_target == 'cloud_run' %}
	uv run uvicorn app.server:app --host 0.0.0.0 --port 8000 --reload
{%- elif cookiecutter.deployment_target == 'agent_engine' %}
	uv export --no-hashes --no-sources --no-header --no-emit-project --frozen > .requirements.txt && uv run app/agent_engine_app.py
{%- endif %}

{% if cookiecutter.deployment_target == 'cloud_run' -%}
ui:
{%- if cookiecutter.agent_name == 'multimodal_live_api' %}
	npm --prefix frontend start
{%- else %}
	uv run streamlit run streamlit/streamlit_app.py --browser.serverAddress=localhost --server.enableCORS=false --server.enableXsrfProtection=false
{%- endif %}
{%- endif %}

lint:
	uv run codespell
	uv run ruff check . --diff
	uv run ruff format . --check --diff
	uv run mypy .
