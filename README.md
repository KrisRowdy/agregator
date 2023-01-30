# agregator
script for defining issues on tests

The algorithm detects the following cases: Flaky tests,
Malfunctioning node, Master branch is broken. Beyond that, the system determines what is
the exact commit that breaks master. For getting all the data samples we use the pandas
python library.
1. Let’s say that a runner is malfunctioning if more than half of test runs are failed. We
will take into account that feature branches are often unstable and at the same time
master itself can be broken. We use a two-stage check to exclude issues connected
with these. We can do so as the chance that all branches will be broken at the same
time is very small. This check is run for each runner.
2. Flaky test is a test that’s result can differ on the same environment without code base
changes. According to the flow, each test isn’t ran twice for the one commit and on
the same node, so we should see broader. For this purpose for each test we will
collect master test results from all runners and sort them by start time. The only
master considering will be enough. Besides, we exclude results from malfunctioning
nodes to the analyzed data set. We count the amount of status changes called
volatility_measure. If the status changes more than 1 time, it means that the test is
flaky.
3. We Can realize that the Master branch is broken when results for any test from all
nodes are failed or volatility_measure = 1 last result is failed.
4. It would be also useful to know which exact commit caused the failure. We can get
this information by searching first commit where success=False
