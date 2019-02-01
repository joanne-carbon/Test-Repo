commitMessage: 'Test RepoUpdater'
branchName: 'test-branch'
includedRepositories:
   - name: 'Test-Repo'
     owner: 'joanne-carbon'
# fileRemoval:
#   - filePaths:  # Delete connections.py file
#     - '**/store/connections.py'
#     removal: true
fileAddition:
  - targetFilePathPattern: '**/src/test.py'
    sourceFilePath: 'test.yaml'
  - targetFilePathPattern: '**/src/test2.py'
    sourceFilePath: 'test.yaml'
