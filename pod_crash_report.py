#!/usr/bin/python3
import requests
import xlsxwriter
import subprocess
import argparse

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--metric", required=True, help="mention metric example: memory, cpu etc")
    ap.add_argument("--duration", required=True, help="number of days example: 1, 7, 30")
    ap.add_argument("--prometheus_url", required=True, help="mention prometheus url example:http://prometheus.example.com:7000")
    ap.add_argument("--container", required=True, help="mention container name example:app-name")
    args = vars(ap.parse_args())
    prometheus_query_basepath="/api/v1/query?query="
    if "*" in str(args['container']):
        prometheus_container_restart_query = "sum without(pod)(increase(kube_pod_container_status_restarts_total{job=\"kube-state-metrics\",container=~\"" + str(args['container']) + "\"}["+ str(args['duration'])  + "d" +"])) > 0"
        prometheus_api_endpoint=str(args['prometheus_url']) + prometheus_query_basepath + prometheus_container_restart_query
    else:
        prometheus_container_restart_query = "sum without(pod)(increase(kube_pod_container_status_restarts_total{job=\"kube-state-metrics\",container=\"" + str(args['container']) + "\"}["+ str(args['duration'])  + "d" +"])) > 0"
        prometheus_api_endpoint=str(args['prometheus_url']) + prometheus_query_basepath + prometheus_container_restart_query
    
    result = crashloop(prometheus_api_endpoint)
    generate_report(result)


def crashloop(prometheus_api_endpoint):
    url = prometheus_api_endpoint
    print(url)
    payload={}
    headers = {}
    response = requests.request("GET", url, headers=headers, data=payload)
    prom_query_output = response.json()
    final_output = []
    for app in prom_query_output['data']['result']:
        restart_count= int(float(app['value'][1]))
        temp_list=[app['metric']['container'],restart_count,find_container_crash_cause(app['metric']['container'])]
        print(temp_list)
        final_output.append(temp_list)
    return(final_output)

def generate_report(result):
    workbook = xlsxwriter.Workbook('Container_Crash_Report.xlsx')
    outSheet = workbook.add_worksheet()
    #Formatting Report
    heading_format = workbook.add_format({
            "bg_color": "#5CB3FF",
            "font": "Century",
            "font_size": 12,
            "bold": True
    })
    #Align - Center
    heading_format.set_align('center')
    #Adjust the column width
    outSheet.set_column(
        "A:C",
        25
    )
    heap_format = workbook.add_format({
        'bg_color': '#A90909',
        'font_color': '#FFFFFF',
        'bold': True
    })
    heap_format.set_align('center')
    other_format = workbook.add_format()
    other_format.set_align('center')
    #write headers
    outSheet.write("A1","Application", heading_format)
    outSheet.write("B1","CrashLoop Count", heading_format)
    outSheet.write("C1","Reason", heading_format)
    #write data to file
    for item in range(len(result)):
        outSheet.write(item+1, 0, result[item][0],other_format)
        outSheet.write(item+1, 1, result[item][1],other_format)
        if result[item][2] == "HEAP_ERR":
            outSheet.write(item+1, 2, result[item][2],heap_format)
        else:
            outSheet.write(item+1, 2, result[item][2],other_format)
    workbook.close()

def find_container_crash_cause(container_name):
    #Get the POD name
    pod_name_command_string = "kubectl get po --all-namespaces | grep " + container_name + " | awk '{print $2}' | head -n 1"
    pod_name_command = subprocess.Popen(
            pod_name_command_string,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    (out, err) = pod_name_command.communicate()
    podid = out.rstrip().decode('ascii')

    #Get the NAMESPACE name
    namespace_name_command_string = "kubectl get po --all-namespaces | grep " + container_name + " | awk '{print $1}' | head -n 1"
    namespace_name_command = subprocess.Popen(
            namespace_name_command_string,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    (out, err) = namespace_name_command.communicate()
    namespaceid = out.rstrip().decode('ascii')

    #Check heap error in previous container logs
    heap_error="\"JavaScript heap out of memory\""
    check_logs_command_string = "kubectl logs -p " + podid + " -n " + namespaceid + " --tail 10 | grep " + heap_error
    check_logs_command = subprocess.Popen(
            check_logs_command_string,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    (out, err) = check_logs_command.communicate()
    logs_output = out.rstrip().decode('ascii')
    rc = check_logs_command.returncode
    print(container_name,": container crashed due to ==>",logs_output)
    #Check OOMKilled container 
    check_oomkilled_command_string = "kubectl describe po " + podid + " -n " + namespaceid + " | grep 'Last State' -A 2 | grep 'Reason' | awk '{print $2}'"
    check_oomkilled_command = subprocess.Popen(
            check_oomkilled_command_string,
            stdout=subprocess.PIPE, stderr=subprocess.DEVNULL, shell=True)
    (out, err) = check_oomkilled_command.communicate()
    oomkilled_output = out.strip().decode('ascii')
    
    if rc == 0:
        return("HEAP_ERR")
    elif oomkilled_output == 'OOMKilled':
        return("CONTAINER_OOM")
    else:
        return("APPLICATION_ISSUES")
if __name__ == '__main__': 
    main()