import requests
import getopt
import sys
from typing import Iterable
from jinja2 import Template
from dataclasses import dataclass


query_user = """
{
  user(login: "{{ githubuser }}") {
    id
  }
}
"""


query_packages = """
{
  user(login: "{{ user }}") {
    repositoriesContributedTo(
      first: 20
{%- if after %}
      after: "{{ after }}"
{%- endif %}
      contributionTypes: [COMMIT]
      includeUserRepositories: true
      orderBy: { field: UPDATED_AT, direction: DESC }
    ) {
      totalCount
      nodes {
        stargazerCount
        nameWithOwner
        url
        owner {
          login
        }
        defaultBranchRef {
            name
            target {
              ... on Commit {
                # total commits on default branch
                history(first: 0) {
                  totalCount
                }
                # commits on default branch authored by jan-janssen
                authorCommits: history(first: 0, author: { id: "{{ userid }}" }) {
                  totalCount
                }
              }
            }
          }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""


@dataclass(frozen=True)
class RepoAttribution:
    repo_full_name: str
    repo_stars: int
    user_commits: int
    total_commits: int
    attributed_stars: float


def get_user_id(username, token):
    t = Template(query_user)
    query = t.render(githubuser=username)
    request = requests.post(
        "https://api.github.com/graphql",
        json={"query": query},
        headers={
            "Authorization": f"Bearer {token}",
            "Accept": "application/vnd.github+json",
            "User-Agent": "github-org-contribs-gql",
        },
    )
    if request.status_code == 200:
        result_dict = request.json()
    else:
        raise Exception(
            "Query failed to run by returning code of {}. {}".format(
                request.status_code, query
            )
        )
    return result_dict["data"]["user"]["id"]


def get_packages(user_name, user_id, token):
    t = Template(query_packages)
    after = None
    next_page = True
    packages_lst = []
    total_list_of_repos = None
    nodes_sum = 0
    while next_page:
        query = t.render(user=user_name, userid=user_id, after=after)
        request = requests.post(
            "https://api.github.com/graphql",
            json={"query": query},
            headers={
                "Authorization": f"Bearer {token}",
                "Accept": "application/vnd.github+json",
                "User-Agent": "github-org-contribs-gql",
            },
        )
        if request.status_code == 200:
            result_dict = request.json()
        else:
            raise Exception(
                "Query failed to run by returning code of {}. {}".format(
                    request.status_code, query
                )
            )
        next_page = result_dict["data"]["user"]["repositoriesContributedTo"][
            "pageInfo"
        ]["hasNextPage"]
        after = result_dict["data"]["user"]["repositoriesContributedTo"]["pageInfo"][
            "endCursor"
        ]
        if total_list_of_repos is None:
            total_list_of_repos = result_dict["data"]["user"][
                "repositoriesContributedTo"
            ]["totalCount"]
        nodes_lst = result_dict["data"]["user"]["repositoriesContributedTo"]["nodes"]
        nodes_sum += len(nodes_lst)
        for repo in nodes_lst:
            stars = repo["stargazerCount"]
            if stars > 0:
                user_commits = repo["defaultBranchRef"]["target"]["authorCommits"][
                    "totalCount"
                ]
                total_commit = repo["defaultBranchRef"]["target"]["history"][
                    "totalCount"
                ]
                packages_lst.append(
                    RepoAttribution(
                        repo_full_name=repo["nameWithOwner"],
                        repo_stars=stars,
                        user_commits=user_commits,
                        total_commits=total_commit,
                        attributed_stars=stars * user_commits / total_commit,
                    )
                )
        print(
            "Downloading: "
            + str(nodes_sum)
            + " / "
            + str(total_list_of_repos)
            + " found "
            + str(len(packages_lst))
            + " repositories with Github stars"
        )
    return packages_lst, total_list_of_repos


def github_hirschfeld_index(attributed_stars_per_repo: Iterable[float]) -> int:
    """
    h = max integer such that at least h repos have attributed_stars >= h.
    Works with fractional stars.
    """
    values = sorted((float(x) for x in attributed_stars_per_repo), reverse=True)
    h = 0
    for i, v in enumerate(values, start=1):
        if v >= i:
            h = i
        else:
            break
    return h


def get_github_hirschfeld_index(username, token):
    user_id = get_user_id(username=username, token=token)
    packages_lst, total_list_of_repos = get_packages(
        user_name=username, user_id=user_id, token=token
    )
    per_repo_sorted = sorted(
        packages_lst, key=lambda r: r.attributed_stars, reverse=True
    )
    return {
        "username": username,
        "repo_count": sum([r.attributed_stars for r in packages_lst]),
        "total_attributed_stars": total_list_of_repos,
        "github_hirschfeld_index": github_hirschfeld_index(
            [r.attributed_stars for r in packages_lst]
        ),
        "per_repo": {r.repo_full_name: r.attributed_stars for r in per_repo_sorted},
    }


def command_line(argv):
    """
    Parses the command line arguments and returns the username, token, and repo.

    Args:
        argv (List[str]): The command line arguments.

    Returns:
        Tuple[str, str, str]: A tuple containing the username, token, and repo.

    Raises:
        GetoptError: If there is an error parsing the command line arguments.
    """
    username = None
    token = None
    template = None
    repository = None
    try:
        opts, args = getopt.getopt(
            argv[1:],
            "u:t:g:r:h",
            ["username=", "token=", "template=", "repository=", "help"],
        )
    except getopt.GetoptError:
        print("run.py -u <username> -t <token> -g <template> -r <repository>")
        sys.exit()
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            print("run.py -u <username> -t <token> -g <template> -r <repository>")
            sys.exit()
        elif opt in ("-u", "--username"):
            username = arg
        elif opt in ("-t", "--token"):
            token = arg
        elif opt in ("-g", "--template"):
            template = arg
        elif opt in ("-r", "--repository"):
            repository = arg
    return username, token, template, repository


if __name__ == "__main__":
    username, token, template, repository = command_line(argv=sys.argv)
    statistics = get_github_hirschfeld_index(
        username=username,
        token=token,
    )

    package_lst = []
    for k, v in statistics["per_repo"].items():
        if int(v) >= 1:
            package_lst.append((k, int(v)))

    with open(template, "r") as f:
        template_content = f.read()

    t = Template(template_content)
    result = t.render(
        username=statistics["username"],
        githubattributedstars=int(statistics["total_attributed_stars"]),
        githubhirsch=int(statistics["github_hirschfeld_index"]),
        package_lst=package_lst,
        repository=repository,
    )

    with open("README.md", "w") as f:
        f.writelines(result)
