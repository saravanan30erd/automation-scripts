# automation-scripts

### Update security group rule

This script is used to automate the updating of one firewall rule in AWS security group,
```shell
    Python3 update-SG-rules.py <IP to allow access> <Security Rule comment> <AWS Security Group>
```
### Generate crashlooping report from Prometheus

The script requires the following:
* Kubernetes with Prometheus Operator Installed. (the script queries kube-state-metrics data)
* Access to Prometheus endpoint and Kubernetes cluster (to execute kubectl commands)
* Python modules needs to be installed on the VM running this script.

Example 
```shell
    ./pod_crash_report.py --metric crashloop --duration 30 --prometheus_url http://localhost:7000 --container "frontend-app.*"

    ./pod_crash_report.py --metric crashloop --duration 60 --prometheus_url http://localhost:7000 --container "queue-app"
```
