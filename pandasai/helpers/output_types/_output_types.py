import re
from decimal import Decimal
from abc import abstractmethod, ABC
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
        return True, ()


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
             { "type": "highchart", "value": { chart: { type: 'line' }, title: { text: 'Simple Line Chart' },
              xAxis: { categories: ['Jan', 'Feb', 'Mar', 'Apr', 'May'] }, 
              yAxis: { title: { text: 'Value' } }, 
              series: [{ name: 'Data Series 1', data: [10, 15, 7, 8, 12] }] 
              }  
              or 
                         
            { "type": "highchart", "value": {     chart: {type: 'pie'},
            title: {
                text: 'Pie Chart Example'
            },
            plotOptions: {
                pie: {
                    allowPointSelect: true,
                    cursor: 'pointer',
                    dataLabels: {
                        enabled: true,
                        format: '<b>{point.name}</b>: {point.percentage:.1f}%'
                    }
                }
            },
            series: [{
                name: 'Brands',
                colorByPoint: true,
                data: [{
                    name: 'Chrome',
                    y: 61.41,
                    sliced: true,
                    selected: true
                }, {
                    name: 'Internet Explorer',
                    y: 11.84
                }, {
                    name: 'Firefox',
                    y: 10.85
                }, {
                    name: 'Edge',
                    y: 4.67
                }, {
                    name: 'Safari',
                    y: 4.18
                }, {
                    name: 'Other',
                    y: 7.05
                }]
            }]
        } 
        or 
    { "type": "highchart", "value": {    chart: {type: 'bubble'},
    title: {
        text: 'Bubble Chart Example'
    },
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
            [78, 37, 34],
            [55, 56, 53],
            [18, 45, 70],
            [42, 44, 28],
            [3, 52, 59],
            [31, 18, 97],
            [79, 91, 63],
            [93, 23, 23],
            [44, 83, 22]
        ]
    }]
    }"""  # noqa E501


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
        return True
