import json
import pandas as pd
import os


def create_dataframe(file):
    """Convert json file to dataframe
    :param file: test runner result json file
    :return: dataframe with columns: "name", "duration", "success", "commit_id", "branch", "started_at", "node"
    """
    json_data = pd.json_normalize(json.loads(file.read()),
                                  "runs",
                                  ["name"])
    # rename the column to avoid duplicated indexes
    json_data.rename(columns={'name': 'node'}, inplace=True)
    json_data = json_data.explode("tests")
    ready_df = pd.concat([json_data.drop(["tests"], axis=1), json_data['tests'].apply(pd.Series)], axis=1)
    return ready_df


def analyze_tests(df, tolerance):
    """Cneck each test history and detect flakiness and master failings
    :param df: resulting dataframe containing the data for all tests running on master for all functional runners
    :param tolerance: the min of status changes indicating flaky test
    :return: flaky tests list and master failed tests dictionary having the form "test": "commit"
    """
    flaky_tests = []
    master_failed_tests = {}
    testlist = df['name'].unique()
    for test in testlist:
        volatility_measure = 0
        test_results_sequence = df[(df.name == test)].sort_values("started_at")[["success", "commit_id"]]
        results_series = (test_results_sequence["success"].tolist())
        size = len(results_series)
        for i in range(1, size):
            if results_series[i] != results_series[i - 1]:
                volatility_measure += 1
        if volatility_measure >= tolerance:
            flaky_tests.append(test)
        elif not results_series[size - 1]:
            # for defining exact commit where fail occurred first time
            exact_commit = test_results_sequence[test_results_sequence.success == False]["commit_id"] \
                .first_valid_index()
            master_failed_tests[test] = exact_commit
    return flaky_tests, master_failed_tests


def check_node(df):
    """Check if runner is malfunctioning
    :param df: dataframe containing test runner results
    :return: True if runner works properly
    """
    total_all = df["name"]
    failed_all = total_all[(df.success == False)]
    total_master = total_all[(df.branch == "master")]
    failed_master = failed_all[(df.branch == "master")]
    return len(failed_master) / len(total_master) < 0.5 and len(failed_all) / len(total_all) < 0.5


def create_summary(failed_nodes, flaky_tests, failed_on_master):
    """Function for creating text for the alert after analyse
    :param failed_nodes: Malfunctioning runners list
    :param flaky_tests: Flaky tests list
    :param failed_on_master: dictionary of commits from that test failed on master
    :return: Text message
    """
    if not failed_nodes and not flaky_tests and not failed_on_master:
        summary = "All tests passed without issues"
    else:
        if failed_nodes:
            summary = "Runner(s) " + str(failed_nodes[0]) + " are malfunctioning.\n"
        if flaky_tests:
            summary += "Test(s) " + str(flaky_tests) + " are flaky.\n"
        if failed_on_master:
            for test, commit in failed_on_master.items():
                summary += "Test " + str(test) + " fails on master after the " + str(commit) + " commit.\n"
    return summary


def aggregator(source_files_location):
    """Main method for detecting issues in tests
    :param source_files_location: location of json test runner results files
    :return: summary information about Flaky tests, Malfunctioning node, Master branch is broken
    """
    file_list = os.listdir(source_files_location)
    main_runners_dfs = []
    failed_nodes = []
    tolerance = 2
    for file in file_list:
        with open('./testruns-data/' + file) as f:
            runner_df = create_dataframe(f)
            is_node_ok = check_node(runner_df)
            if is_node_ok:
                main_runners_dfs.append(runner_df[(runner_df.branch == "master")])
            else:
                failed_nodes.append(runner_df["node"].unique())
    united_df = pd.concat(main_runners_dfs, sort=False)
    flaky_tests, failed_on_master = analyze_tests(united_df, tolerance)
    summary = create_summary(failed_nodes, flaky_tests, failed_on_master)
    print(summary)
    return summary


if __name__ == "__main__":
    aggregator('./testruns-data')
