import json

refactorings = [
    "Chained Tests", "Database Sandbox", "Delegated Setup", "Delta Assertion",
    "Garbage Collected Teardown", "Guard Assertion", "Implicit Setup",
    "Implicit Teardown", "Inline Setup", "Inline Teardown", "Lazy Setup",
    "Named Test Suite", "Parameterized Test", "Prebuilt Fixture",
    "Setup Decorator", "Shared Fixture", "Stored Procedure Test",
    "Suite Fixture Setup", "Table Truncation Teardown", "Test Helper",
    "Custom Assertion", "Verification Method", "Test Specific Subclass",
    "Testcase Superclass", "Transaction Rollback Teardown",
    "Extract Testable Component", "In-line Resource", "Make Resource Unique",
    "Minimize Data", "Replace Dependency with Test Double",
    "Setup External Resource", "Lambdarize Method", "Delambdarize Method",
    "Delete Mock Object", "Change Assertion Type", "Split Test Method",
    "Merge Test Method", "Grouping Tests", "Assert All", "Add Cleanup Method",
    "Replace annotation with try/catch", "Replace try/catch with annotation",
    "Replace try/catch with asserThrows", "Replace assertThrow with try/catch",
    "Replace assertThrow with annotation"
]

template = {
    "name": "",
    "description": "",
    "tags": [],
    "before": {
        "method": {
            "type": "MethodDeclaration",
            "multiple": True,
            "required": False,
            "autofills": [
                {
                    "type": "Surround",
                    "element": "MethodDeclaration",
                    "follows": [
                        {
                            "name": "method before",
                            "category": "before"
                        }
                    ]
                }
            ],
            "description": ""
        },
        "invocation": {
            "type": "MethodInvocation",
            "multiple": True,
            "required": False,
            "description": "method invocation"
        },
        "code fragment": {
            "type": "CodeFragment",
            "multiple": True,
            "required": False,
            "description": "code fragment"
        }
    },
    "after": {
        "method": {
            "type": "MethodDeclaration",
            "multiple": True,
            "required": False,
            "autofills": [
                {
                    "type": "Surround",
                    "element": "MethodDeclaration",
                    "follows": [
                        {
                            "name": "method after",
                            "category": "after"
                        }
                    ]
                }
            ],
            "description": ""
        },
        "invocation": {
            "type": "MethodInvocation",
            "multiple": True,
            "required": False,
            "description": "method invocation"
        },
        "code fragment": {
            "type": "CodeFragment",
            "multiple": True,
            "required": False,
            "description": "code fragment"
        }
    }
}

# JSON データのリストを作成
json_data = []
for refactoring in refactorings:
    entry = template.copy()
    entry["name"] = refactoring
    entry["tags"] = refactoring.split()
    json_data.append(entry)

# JSONファイルとして保存
with open("refactoring_methods.json", "w", encoding="utf-8") as f:
    json.dump(json_data, f, indent=2, ensure_ascii=False)

print("JSONファイル 'refactoring_methods.json' を作成しました。")