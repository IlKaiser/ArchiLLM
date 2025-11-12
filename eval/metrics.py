import pandas as pd
import json

def single_quote_to_double(str_in) -> str:
    """
    A function to parse a string and convert it into a valid JSON format.
    It replaces single quotes with double quotes
    """
    # Replace single quotes with double quotes except when they are inside double quotes.
    opend = False
    str_out = ""
    for c in str_in:
        if c != "'":
            if c == '"' and not opend:
                opend = True
            elif c == '"' and opend:
                opend = False
            str_out += c
        else:
            if opend:
                str_out += c
            else:
                str_out += '"'
    
  
    
    return str_out

def compute_microservice_lack(ms, num_params):
    inputs = ms.get("inputs", [])
    outputs = ms.get("outputs", [])
    parameters = ms.get("parameters", [])
    endpoints = ms.get("endpoints", [])

    all_params = inputs + outputs + parameters
    num_unique_params = len(set(all_params))
    num_endpoints = len(endpoints)
    
    if num_endpoints == 0 or num_unique_params == 0:
        return 1.0

    return max(0, round(1 - (num_params / (num_endpoints * num_unique_params)), 4))

def compute_system_lack_of_cohesion(judged_microservices):
    # compute total number of endpoints in ms
    num_endpoints = sum(len(ms.get("endpoints", [])) for ms in judged_microservices)
    
    scores = [compute_microservice_lack(ms, num_endpoints) for ms in judged_microservices]
    if not scores:
        return None
    return round(sum(scores) / len(scores), 4)



METHODS_WEIGHT = {
    "GET": 1,
    "POST": 4,
    "PUT": 3,
    "DELETE": 2,
    "PATCH": 3
}

def compute_data_granularity(endpoint, fp, cp):
    """Compute the data granularity score for a given endpoint."""
    inputs = len(endpoint.get("inputs", []))
    outputs = len(endpoint.get("outputs", []))

    if fp == 0 or cp == 0:
        return 0
    
    print(f"Inputs: {inputs}, Outputs: {outputs}, FP: {fp}, CP: {cp}")
    print("DGS:", round((inputs/fp + outputs/cp), 4))

    return min(1, round( ((inputs/fp) + (outputs/cp)), 4))  

def compute_function_granularity(endpoint, o):
    """Compute the function granularity score for a given endpoint."""
    method_weight = METHODS_WEIGHT.get(endpoint.get("method", "").upper(), 0)
    if o == 0:
        return 0
    
    print(f"Method Weight: {method_weight}, O: {o}")
    print("FGS:", round(method_weight / o, 4))

    return min(1, round(method_weight / o, 4))

def compute_service_granularity_metric(ms):
    """Compute the service granularity metric for a microservice."""
    fp = sum(len(ep.get("inputs", [])) for ep in ms["endpoints"])
    cp = sum(len(ep.get("outputs", [])) for ep in ms["endpoints"])

    o = sum(METHODS_WEIGHT.get(ep.get("method", "").upper(), 0) for ep in ms["endpoints"])

    tot_sgm = 0
    for ep in ms["endpoints"]:
        dgs = compute_data_granularity(ep, fp, cp)
        fgs = compute_function_granularity(ep, o)

        sgm = (dgs * fgs)
        tot_sgm += sgm
        print(f"Endpoint: {ep['name']}, DGS: {dgs}, FGS: {fgs}, SGM: {sgm}")

    return tot_sgm

def compute_average_service_granularity(microservices):
    """Compute the average service granularity for a list of microservices."""
    if not microservices:
        return 0

    total_sgm = sum(compute_service_granularity_metric(ms) for ms in microservices)
    return round(total_sgm / len(microservices), 4) if total_sgm else 0

def compute_metrics_from_excel(excel_path: str, output_path: str = "with_lack_of_cohesion.xlsx"):
    df = pd.read_excel(excel_path)

    lack_values = []
    asgm_values = []

    for _, row in df.iterrows():
        try:
            try:
                output_data = json.loads(row["Dalle Output"])
            except json.JSONDecodeError:
                output_data = json.loads(single_quote_to_double(row["Dalle Output"]))
            microservices = output_data["microservices"]
            score = compute_system_lack_of_cohesion(microservices)
            asgm = compute_average_service_granularity(microservices)
            
            
        except Exception:
            score = None
        lack_values.append(score)
        asgm_values.append(asgm)


    df["lack_of_cohesion"] = lack_values
    df["average_service_granularity"] = asgm_values
    df.to_excel(output_path, index=False)
    print(f"Saved output with cohesion metrics to: {output_path}")


if __name__ == "__main__":
    compute_metrics_from_excel("/Users/marcocalamo/ARCHILLM/results_student.xlsx", output_path="stud_metrics.xlsx")