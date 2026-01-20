# My Github Hirsch Index

[![Deploy](https://github.com/{{ repository }}/workflows/Deploy/badge.svg)](https://github.com/{{ repository }}/actions)

| Username    | Attributed Github Stars | Github Hirsch Index |
|-------------|------------------------:|------------------------:|
| [{{ username }}](https://github.com/{{ username }}) | {{ githubattributedstars }} :star: | {{ githubhirsch }} :zap: |

## Repositories 

| Repository | Attributed Github Stars | Total Github Stars |
|------------|------------------------:|-------------------:|
{% for package in package_lst -%}
{% if package[1] >= githubhirsch -%}
| [**{{ package[0] }}**](https://github.com/{{ package[0] }}) | {{ package[1] }} :star: | ![GitHub Repo stars](https://img.shields.io/github/stars/{{ package[0] }}) |
{%- else -%}
| [{{ package[0] }}](https://github.com/{{ package[0] }}) | {{ package[1] }} :star: | ![GitHub Repo stars](https://img.shields.io/github/stars/{{ package[0] }}) |
{%- endif %}
{% endfor %}

## Calculate your Github Hirsch Index

* [Fork this repository](https://github.com/jan-janssen/My-Github-Hirsch-Index/fork).
* Go to the repository `Settings` on the page for `Actions` at the top under `Actions permissions` set `Allow all actions and reusable workflows` to enable the Github actions for this repository.
* Finally, under `Settings` on the page for `Actions` at the bottom also set the `Workflow permissions` to `Read and write permissions` to enable uploading the calculated Github Hirsch Index.
