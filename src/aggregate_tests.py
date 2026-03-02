import os
import json
import glob
from xml.etree import ElementTree as ET
from urllib.parse import unquote

def parse_json_report(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        if 'summary' in data:
            summary = data['summary']
            return {
                'total': summary.get('total', 0),
                'passed': summary.get('passed', 0),
                'failed': summary.get('failed', 0),
            }
    except Exception as e:
        print(f"Error parsing JSON {file_path}: {e}")
    return None

def parse_xml_reports(report_dir):
    xml_files = glob.glob(os.path.join(report_dir, 'TEST-*.xml'))
    if not xml_files:
        return None
    
    total = 0
    passed = 0
    failed = 0
    errors = 0
    skipped = 0
    
    for file_path in xml_files:
        try:
            tree = ET.parse(file_path)
            root = tree.getroot()
            if root.tag == 'testsuite':
                t_tests = int(root.attrib.get('tests', 0))
                t_failures = int(root.attrib.get('failures', 0))
                t_errors = int(root.attrib.get('errors', 0))
                t_skipped = int(root.attrib.get('skipped', 0))
                
                total += t_tests
                failures = t_failures + t_errors
                failed += failures
                skipped += t_skipped
                passed += (t_tests - failures - t_skipped)
        except Exception as e:
            print(f"Error parsing XML {file_path}: {e}")
    
    if total == 0 and not xml_files:
        return None
        
    return {
        'total': total,
        'passed': passed,
        'failed': failed,
        'skipped': skipped
    }

def main():
    projects_dir = os.path.join(os.getcwd(), 'projects')
    if not os.path.exists(projects_dir):
        print(f"Projects directory not found at {projects_dir}")
        return

    results = {}

    for root, dirs, files in os.walk(projects_dir):
        # Prevent digging into node_modules or standard target folders if unnecessary
        if 'node_modules' in dirs:
            dirs.remove('node_modules')

        # Check for JSON reports
        if os.path.basename(root) == 'report':
            json_files = [f for f in files if f.endswith('.json')]
            if json_files:
                # Find the latest by file name sorting
                json_files.sort(reverse=True)
                latest_report = os.path.join(root, json_files[0])
                stats = parse_json_report(latest_report)
                if stats:
                    # Deduce project name from path
                    parts = root.split(os.sep)
                    # projects / <project_name> / ... / report
                    try:
                        proj_idx = parts.index('projects')
                        project_name = parts[proj_idx + 1]
                        results[project_name] = stats
                    except ValueError:
                        results[root] = stats
                        
        # Check for XML Surefire reports
        elif os.path.basename(root) == 'surefire-reports':
            stats = parse_xml_reports(root)
            if stats:
                parts = root.split(os.sep)
                try:
                    proj_idx = parts.index('projects')
                    project_name = parts[proj_idx + 1]
                    # If we already have JSON results for this project (unlikely but possible), let's prioritize or merge.
                    # Usually it's either/or.
                    if project_name not in results:
                        results[project_name] = stats
                except ValueError:
                    results[root] = stats

    print("==================================================")
    print(f"{'Project':<25} | {'Total':<6} | {'Passed':<6} | {'Failed':<6} | {'Pass Rate':<8}")
    print("==================================================")
    
    total_all = 0
    passed_all = 0
    failed_all = 0
    
    for proj, stats in sorted(results.items()):
        total = stats.get('total', 0)
        passed = stats.get('passed', 0)
        failed = stats.get('failed', 0)
        
        total_all += total
        passed_all += passed
        failed_all += failed
        
        rate = (passed / total * 100) if total > 0 else 0.0
        print(f"{proj:<25} | {total:<6} | {passed:<6} | {failed:<6} | {rate:6.2f}%")

    print("==================================================")
    overall_rate = (passed_all / total_all * 100) if total_all > 0 else 0.0
    print(f"{'OVERALL':<25} | {total_all:<6} | {passed_all:<6} | {failed_all:<6} | {overall_rate:6.2f}%")
    print("==================================================")

if __name__ == '__main__':
    main()
