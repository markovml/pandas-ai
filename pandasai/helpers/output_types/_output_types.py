import re
from abc import ABC, abstractmethod
from decimal import Decimal
from typing import Any, Iterable

from ..df_info import df_type


class BaseOutputType(ABC):
    @property
    @abstractmethod
    def template_hint(self) -> str:
        ...

    @property
    @abstractmethod
    def name(self) -> str:
        ...

    def _validate_type(self, actual_type: str) -> bool:
        return actual_type == self.name

    @abstractmethod
    def _validate_value(self, actual_value):
        ...

    def validate(self, result: dict[str, Any]) -> tuple[bool, Iterable[str]]:
        """
        Validate 'type' and 'value' from the result dict.

        Args:
            result (dict[str, Any]): The result of code execution in
                dict representation. Should have the following schema:
                {
                    "type": <output_type_name>,
                    "value": <generated_value>
                }

        Returns:
             (tuple(bool, Iterable(str)):
                Boolean value whether the result matches output type
                and collection of logs containing messages about
                'type' or 'value' mismatches.
        """
        validation_logs = []
        actual_type, actual_value = result.get("type"), result.get("value")

        type_ok = self._validate_type(actual_type)
        if not type_ok:
            validation_logs.append(
                f"The result dict contains inappropriate 'type'. "
                f"Expected '{self.name}', actual '{actual_type}'."
            )
        value_ok = self._validate_value(actual_value)
        if not value_ok:
            validation_logs.append(
                f"Actual value {repr(actual_value)} seems to be inappropriate "
                f"for the type '{self.name}'."
            )

        return all((type_ok, value_ok)), validation_logs


class NumberOutputType(BaseOutputType):
    @property
    def template_hint(self):
        return """type (must be "number"), value must int. Example: { "type": "number", "value": 125 }"""  # noqa E501

    @property
    def name(self):
        return "number"

    def _validate_value(self, actual_value: Any) -> bool:
        return isinstance(actual_value, (int, float, Decimal))


class DataFrameOutputType(BaseOutputType):
    @property
    def template_hint(self):
        return """type (must be "dataframe"), value must be pd.DataFrame or pd.Series. Example: { "type": "dataframe", "value": pd.DataFrame({...}) }"""  # noqa E501

    @property
    def name(self):
        return "dataframe"

    def _validate_value(self, actual_value: Any) -> bool:
        return bool(df_type(actual_value))


class PlotOutputType(BaseOutputType):
    @property
    def template_hint(self):
        return """type (must be "plot"), value must be string. Example: { "type": "plot", "value": "temp_chart.png" }"""  # noqa E501

    @property
    def name(self):
        return "plot"

    def _validate_value(self, actual_value: Any) -> bool:
        if not isinstance(actual_value, str):
            return False

        path_to_plot_pattern = r"^(\/[\w.-]+)+(/[\w.-]+)*$|^[^\s/]+(/[\w.-]+)*$"
        return bool(re.match(path_to_plot_pattern, actual_value))


class StringOutputType(BaseOutputType):
    @property
    def template_hint(self):
        return """type (must be "string"), value must be string. Example: { "type": "string", "value": f"The highest salary is {highest_salary}." }"""  # noqa E501

    @property
    def name(self):
        return "string"

    def _validate_value(self, actual_value: Any) -> bool:
        return isinstance(actual_value, str)


class DefaultOutputType(BaseOutputType):
    default_types = ["string", "number", "dataframe", "plot"]

    @property
    def template_hint(self):
        return """type (possible values "string", "number", "dataframe", "plot"). Examples: { "type": "string", "value": f"The highest salary is {highest_salary}." } or { "type": "number", "value": 125 } or { "type": "dataframe", "value": pd.DataFrame({...}) } or { "type": "plot", "value": "temp_chart.png" }"""  # noqa E501

    @property
    def name(self):
        return "default"

    def _validate_type(self, actual_type: str) -> bool:
        return True

    def _validate_value(self, actual_value: Any) -> bool:
        return True

    def validate(self, result: dict[str, Any]) -> tuple[bool, Iterable]:
        """
        Validate 'type' and 'value' from the result dict.

        Returns:
             (bool): True since the `DefaultOutputType`
                is supposed to have no validation
        """
        return result["type"] in self.default_types, ()


class MKVDefaultOutputType(DefaultOutputType):
    @property
    def template_hint(self):
        return """type (possible values "string", 
        "number", "dataframe", "highchart config").
         Examples: 
             { "type": "string", "value": f"The highest salary is {highest_salary}." } 
             or 
             { "type": "number", "value": 125 } 
             or 
             { "type": "dataframe", "value": pd.DataFrame({...}) } 
             or 
             { "type": "highchart", "value": { chart: { type: 'line' }, 
              title: { text: 'Simple Line Chart' },
              xAxis: { categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May'] }, 
              yAxis: { title: { text: 'Value' } }, 
              series: [{ name: 'Data Series 1', data: [10, 15, 7, 8, 12] }] 
              }  
            or 
            { "type": "highchart", "value": {chart: {type: 'heatmap'},
            title: { text: 'Simple Heatmap Chart' },
            colorAxis: {
                stops: [
                    [0, '#4e79a7'], // Lightest color
                    [0.5, '#f28e2c'], // Middle color
                    [1, '#e15759'] // Darkest color
                ]
            },
            xAxis: {
                categories: ['Category 1', 'Category 2', 'Category 3'] // X-axis categories
            },
            yAxis: {
                categories: ['Label 1', 'Label 2', 'Label 3'], // Y-axis categories
                title: null
            },
            series: [{
                data: [
                    [0, 0, 10], // x, y, value
                    [0, 1, 20],
                    [0, 2, 30],
                    [1, 0, 40],
                    [1, 1, 50],
                    [1, 2, 60],
                    [2, 0, 70],
                    [2, 1, 80],
                    [2, 2, 90]
                ],
                dataLabels: {
                    enabled: true,
                    color: '#000000'
                }
            }]
            }
            or
        { "type": "highchart", "value": { chart: {type: 'bubble'},
          title: {text: 'Bubble Chart Example'},
        xAxis: {
        title: {
            text: 'X-axis'
        }
        },
        yAxis: {
            title: {
                text: 'Y-axis'
            }
        },
    series: [{
        data: [
            [9, 81, 63],
            [98, 5, 89],
            [51, 50, 73],
            [41, 22, 14],
            [58, 24, 20],
            [78, 37, 34]
        ]
    }]
         }  
    or 
    { "type": "highchart", "value": { chart: {type: 'pie'},
    title: { text: 'Simple Pie Chart' },
    series: [{
        data: [
            ['Chrome', 61.41],
            ['Firefox', 10.85],
            ['Edge', 4.67],
            ['Safari', 4.18],
            ['Other', 7.05]
        ]
    }]
    }}
    or
    {"type":"highchart","value":{    chart: {type: 'table'},
    title: {text: 'Table Example'},
    xAxis: {
        categories: ['Category 1', 'Category 2', 'Category 3']
    },
    yAxis: {
        visible: false
    },
    series: [{
        name: 'Label 1',
        data: [10, 20, 30]
    }, {
        name: 'Label 2',
        data: [40, 50, 60]
    }, {
        name: 'Label 3',
        data: [70, 80, 90]
    }]}  
    """  # noqa E501


class HighChartOutputType(BaseOutputType):
    @property
    def template_hint(self):
        return """type (must be "highchart"), value must be highchart config. 
        Example: { "type": "highchart", "value": { chart: { type: 'line' }, 
        title: { text: 'Simple Line Chart' }, xAxis: { categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May'] },
         yAxis: { title: { text: 'Value' } }, series: [{ name: 'Data Series 1', data: [10, 15, 7, 8, 12] }] } }"""  # noqa E501

    @property
    def name(self):
        return "highchart"

    def _validate_value(self, actual_value: Any) -> bool:
        return isinstance(actual_value, dict)
