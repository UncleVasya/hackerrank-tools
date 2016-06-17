import requests
import json
import os
import tarfile
import tempfile
import argparse
from globster import Globster


def build_arhive():
    print 'Making archive...'

    root = os.path.dirname(os.path.realpath(__file__))

    # respect .gitignore files
    gitignores = ['.gitignore', '../.gitignore']
    excluded = []
    for g in gitignores:
        path = os.path.join(root, g)
        with open(path) as f:
            ignored = filter(None, f.read().split('\n'))
        excluded.extend(ignored)

    print 'Excluded: %s' % excluded

    globster = Globster(excluded)

    def is_excluded(path):
        relpath = os.path.relpath(path, start=root)
        return globster.match(relpath)

    archive = tempfile.NamedTemporaryFile(delete=False)
    with tarfile.open(fileobj=archive, mode='w', dereference=True) as tar:
        tar.add(root, arcname='', exclude=is_excluded)
    archive.close()

    print 'Archive created: '

    return archive.name


def upload_archive(archive_path, app):
    api_url = 'https://api.heroku.com/apps/%s/' % app
    sources_url = api_url + 'sources'
    builds_url = api_url + 'builds'

    headers = {
        'Accept': 'application/vnd.heroku+json; version=3',
        'Content-Type': 'application/json',
    }

    print 'Getting url for upload...'

    r = requests.post(sources_url, headers=headers)
    data = r.json()['source_blob']

    get_url = data['get_url']
    put_url = data['put_url']

    print 'Uploading archive...'

    with open(archive_path, 'r') as f:
        archive = f.read()
    requests.put(put_url, data=archive)

    print 'Creating build...'

    data = {
        'source_blob': {
            'url': get_url,
        }
    }
    r = requests.post(builds_url, headers=headers, data=json.dumps(data))
    data = r.json()
    print '\nHeroku response:\n%s\n' % data


def deploy_archive(app):
    print '\nDeploying to %s' % app

    path = build_arhive()
    upload_archive(path, app)
    os.unlink(path)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="""
        This script tarballs website folder
        and uploads it to Heroku as a new build.

        - respects global and website .gitignore files;
        - symlinks replaced with actual data;
    """, formatter_class=argparse.RawTextHelpFormatter)

    parser.add_argument('-a', '--app', help='Name of app on Heroku', required=True)
    args = parser.parse_args()

    deploy_archive(args.app)
