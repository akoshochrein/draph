import argparse
import requests
import pprint

from collections import defaultdict


parser = argparse.ArgumentParser(description="""
    Build a dependency graph out of the detectable requirements in your complex python projects
""".strip())
parser.add_argument('githubtoken',
    help="Valid Github token that the script can use to scrape your repositories"
)


def dependencies_cleaner(dependencies):
    clean_dependencies = []
    clean_dependencies = filter(len, dependencies)
    clean_dependencies = filter(lambda s: not s.startswith('#'), clean_dependencies)
    clean_dependencies = filter(lambda s: 'git+git@github.com' not in s, clean_dependencies)
    return clean_dependencies


def dependency_parser(parent, dependencies, known_dependencies, githubtoken):
    for dependency in dependencies:
        if dependency not in known_dependencies:
            name = dependency.split('==')[0]
            parts = name.split('-')
            known_dependencies[parent].append(name)
            if len(parts) > 1:
                headers = {
                    'Authorization': 'token {token}'.format(token=githubtoken),
                    'Accept': 'application/vnd.github.v3.raw'
                }
                url = 'https://api.github.com/{user_name}/{repo_name}/master/requirements.txt'.format(
                    user_name=parts[0],
                    repo_name='-'.join(parts[1:]),
                )
                response = requests.get(url, headers=headers)
                if response.status_code == 404:
                    if name == 'prezi-utils':
                        import pdb; pdb.set_trace()
                    url = 'https://raw.githubusercontent.com/{user_name}/{repo_name}/master/requirements.txt'.format(
                        user_name=parts[0],
                        repo_name='-'.join(parts),
                    )

                response = requests.get(url, headers=headers)
                if response.status_code == 200:
                    dependency_parser(
                        name,
                        dependencies_cleaner(response.content.decode().split('\n')),
                        known_dependencies,
                        githubtoken
                    )


def run():
    dependency_graph = defaultdict(list)

    args = parser.parse_args()
    with open('requirements.txt', 'r') as f:
        dependency_parser(
            'root',
            dependencies_cleaner(f.read().split('\n')),
            dependency_graph,
            args.githubtoken
        )

    pprint.pprint(dependency_graph)
