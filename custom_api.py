import json

class CustomApi:

    def __init__(self):
        self.functions = [
            {
                "name": "get_current_weather", # 函數名，與def的函數名稱相關
                "description": "Get the current weather", # 函數的描述
                "parameters": { # 函數的所需參數，對於需求參數的描述
                    "type": "object",
                    "properties": {
                        "location": {
                            "type": "string", # 類型
                            "description": "台灣城市名稱",
                        },
                        "format": {
                            "type": "string",
                            "enum": ["celsius", "fahrenheit"],
                            "description": "溫度的格式",
                        },
                    },
                    "required": ["location", "format"], # 哪些參數需要
                },
            },
        ]

    def get_current_weather(self, location, unit="Celsius"):
        """Get the current weather in a given location"""
        weather_info = {
            "location": location,
            "temperature": "30",
            "unit": unit,
            "forecast": ["sunny", "windy"],
        }
        result = json.dumps(weather_info)
        return result
    
    def execute_function(self, fn_name, arguments):
        "執行相對應的API"
        dict = {
            "get_current_weather": self.get_current_weather,
            "get_collection": self.get_collection,
            "ready_to_work": self.ready_to_work,
        }

        function_to_call = dict[fn_name] 

        function_args = json.loads(arguments)
        function_response = function_to_call(**function_args)

        return function_response