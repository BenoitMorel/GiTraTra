import os
import sys
from github import Github
import pickle

"""
  db[repository]["clone" or "view"][timestamp] -> Clone or View object
"""

def get_db(db_path):
  if (not os.path.isfile(db_path)):
    return {}
  else:
    with open(db_path, 'rb') as handle:
      return pickle.load(handle)

def save_db(db_path, db):
  print("Saving results...")
  with open(db_path, 'wb') as handle:
    pickle.dump(db, handle, protocol=pickle.HIGHEST_PROTOCOL)

def update_repo(repo, db):
  if (not repo.name in db):
    db[repo.name] = {}
    db[repo.name]["clones"] = {}
    db[repo.name]["views"] = {}
  print("querying current traffic data from " + repo.name + "...")
  # clones
  clones = repo.get_clones_traffic()["clones"]
  per_stamp_clones = db[repo.name]["clones"]
  for clone in clones: 
    per_stamp_clones[clone.timestamp] = clone
  # views
  views = repo.get_views_traffic()["views"]
  per_stamp_views = db[repo.name]["views"]
  for view in views: 
    per_stamp_views[view.timestamp] = view

def print_clones(db):
  print("")
  for repo_name in db:
    print(repo_name)
    total_uniques_clones = 0
    total_uniques_views = 0
    total_clones = 0
    total_views = 0
    per_stamp_clones = db[repo_name]["clones"]
    for stamp in per_stamp_clones:
      #print(str(stamp) + ":" + str(per_stamp_clones[stamp].uniques))
      total_uniques_clones += per_stamp_clones[stamp].uniques
      total_clones += per_stamp_clones[stamp].count
    per_stamp_views = db[repo_name]["views"]
    for stamp in per_stamp_views:
      total_uniques_views += per_stamp_views[stamp].uniques
      total_views += per_stamp_views[stamp].count
    print("clones: " + str(total_clones))
    print("unique clones: " + str(total_uniques_clones))
    #print("views: " + str(total_views))
    #print("unique views: " + str(total_uniques_views))
    print("")

def get_repositories(repositories_file_path):
  res = []
  lines = open(repositories_file_path).readlines()
  for line in lines:
    strip = line.strip()
    if (len(strip) > 0):
      res.append(strip)
  return res

def run_gitratra(token, db_path, repositories_file_path):
  print("Authentification...")
  g = Github(token)
  repositories = get_repositories(repositories_file_path)
  db = get_db(db_path)
  for repo_name in repositories:
    repo = g.get_user().get_repo(repo_name)
    update_repo(repo, db)
  print_clones(db)
  save_db(db_path, db)

if (__name__== "__main__"):
  if (len(sys.argv) != 4):
    print("Syntax error: python run_generax.py auth_token repositories_list_file output_file.")
    sys.exit(0)

token = sys.argv[1]
repositories_file_path = sys.argv[2]
db_path = sys.argv[3]
run_gitratra(token, db_path, repositories_file_path)

