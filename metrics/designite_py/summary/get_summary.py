# Given the NEW and OLD dpy folder paths (NEW one comes first!) (Only the old one is available in the first checkpoint)
# Return the summary
import os
import json


def _format_change(number):
    return f"+{number}" if number > 0 else str(number)


def _get_summary_metrics(dpy_folder):
    n, nom, nopm, cc = 0, 0, 0, 0
    for json_file in os.listdir(dpy_folder):
        # class module metrics
        if json_file.endswith("class_module_metrics.json"):
            with open(os.path.join(dpy_folder, json_file), "r") as f:
                # Filter out __init__.py. May add more files such as __main__.py later
                class_json = [x for x in (json.load(f)) if x["Module"] != "__init__"]
                loc = sum([x["LOC"] for x in class_json])
                n = len(set(x["Module"] for x in class_json))
                nom = (
                    sum([x["NOM"] for x in class_json]) / len(class_json)
                    if len(class_json) > 0
                    else 0
                )
                nopm = (
                    sum([x["NOPM"] for x in class_json]) / len(class_json)
                    if len(class_json) > 0
                    else 0
                )

        # function metrics
        if json_file.endswith("function_metrics.json"):
            with open(os.path.join(dpy_folder, json_file), "r") as f:
                function_json = json.load(f)
                cc = (
                    sum([x["CC"] for x in function_json]) / len(function_json)
                    if len(function_json) > 0
                    else 0
                )

    return {
        "n": n,
        "loc": loc,
        "nom": round(nom, 2),
        "nopm": round(nopm, 2),
        "cc": round(cc, 2),
    }


def get_dpy_summary(dpy_folder_new, dpy_folder_old=None):
    """
    Return in the format [
        {
            "number_of_modules": {
                "new_value": 20,
                "change": "+4"
            },
            "lines_of_code": {
                "new_value": 20,
                "change": "+4
            },
            "number_of_methods_per_module": {
                "new_value": 20,
                "change": "+4"
            },
            "number_of_public_methods_per_module": {
                "new_value": 20,
                "change": "+4"
            },
            "cyclomatic_complexity_per_function": {
                "new_value": 20,
                "change": "-4"
            }
        }
    ]

    Change is only available if the design json new is available.
    """
    new_metrics = _get_summary_metrics(dpy_folder=dpy_folder_new)
    if dpy_folder_old:
        old_metrics = _get_summary_metrics(dpy_folder=dpy_folder_old)

    summary = {
        "number_of_modules": {"new_value": new_metrics["n"]},
        "lines_of_code": {"new_value": new_metrics["loc"]},
        "number_of_methods_per_module": {
            "new_value": new_metrics["nom"],
        },
        "number_of_public_methods_per_module": {
            "new_value": new_metrics["nopm"],
        },
        "cyclomatic_complexity_per_function": {
            "new_value": new_metrics["cc"],
        },
    }

    # add the changed values also if the old folder is present
    if dpy_folder_old:
        n_change = round(new_metrics["n"] - old_metrics["n"], 2)
        loc_change = round(new_metrics["loc"] - old_metrics["loc"], 2)
        nom_change = round(new_metrics["nom"] - old_metrics["nom"], 2)
        nopm_change = round(new_metrics["nopm"] - old_metrics["nopm"], 2)
        cc_change = round(new_metrics["cc"] - old_metrics["cc"], 2)

        summary["number_of_modules"]["change"] = _format_change(n_change)
        summary["lines_of_code"]["change"] = _format_change(loc_change)
        summary["number_of_methods_per_module"]["change"] = _format_change(nom_change)
        summary["number_of_public_methods_per_module"]["change"] = _format_change(
            nopm_change
        )
        summary["cyclomatic_complexity_per_function"]["change"] = _format_change(
            cc_change
        )

    return summary
