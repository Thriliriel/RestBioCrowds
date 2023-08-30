$procs = $(
Start-Process python ".\LocalExperiment.py --p .\ExperimentsData\Scenario1 --c 3 --s 0 --e 50"-PassThru;
Start-Process python ".\LocalExperiment.py --p .\ExperimentsData\Scenario2 --c 3 --s 0 --e 50" -PassThru;
Start-Process python ".\LocalExperiment.py --p .\ExperimentsData\Scenario3 --c 3 --s 0 --e 30" -PassThru;
Start-Process python ".\LocalExperiment.py --p .\ExperimentsData\Scenario4 --c 4 --s 0 --e 20" -PassThru;
Start-Process python ".\LocalExperiment.py --p .\ExperimentsData\Scenario5 --c 3 --s 0 --e 20" -PassThru;
)

$procs | Wait-Process

Read-Host -Prompt "Press Enter to continue"