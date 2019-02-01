commitMessage: 'Test RepoUpdater'
branchName: 'test-branch'
includedRepositories:
  - name: 'Test-Repo'
    owner: 'joanne-carbon'
fileModifications:
  - filePaths:
    - '**/test.py'
    replacements:
      - regexPattern: 'boo'
        replaceWith: 'yaa'
# fileRemoval:
#   filePaths:  # Delete connections.py file
#     - '**/store/connections.py'
#     - '**/test.py'
fileAddition:
  - targetFilePathPattern: '**/src/test.py'
    sourceFilePath: 'test.yaml'
  - targetFilePathPattern: '**/src/test2.py'
    sourceFilePath: 'test.yaml'
