import io
import time
import os
import numpy as np
import pandas as pd
from product.models import Paramters, RuntimeParameterValues
from product.services.generic_services import read_csv_from_s3


import boto3
from dotenv import load_dotenv, find_dotenv

load_dotenv(find_dotenv())
AWS_ACCESS_KEY_ID = os.environ.get('AWS_ACCESS_KEY_ID')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
AWS_DEFAULT_REGION = os.environ.get('AWS_DEFAULT_REGION')

session = boto3.Session(
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_DEFAULT_REGION  # Override default region
)
s3 = session.client('s3')

class Condition:
    """
    A class to represent a condition that can be applied to a DataFrame.

    Attributes:
        check_key (str): The key (column name) in the DataFrame to apply the condition.
        check_type (str): The type of condition to apply (e.g., 'in', 'exact', 'iexact', etc.).
        check_value (Any): The value to compare against in the condition.
        is_mandatory (bool, optional): Whether the condition is mandatory. Defaults to True.
        skip_if_no_column (bool, optional): Whether to skip the condition if the column does not exist. Defaults to False.

    Methods:
        __init__(self, check_key, check_type, check_value, is_mandatory=True, skip_if_no_column=False):
            Initializes a new instance of the Condition class.
        apply(self, df, safe_str_accessor):
            Applies the condition to the given DataFrame.
    """

    def __init__(self, check_key, check_type, check_value, is_mandatory=True, skip_if_no_column=False):
        """
        Initializes a new instance of the Condition class.

        Args:
            check_key (str): The key (column name) in the DataFrame to apply the condition.
            check_type (str): The type of condition to apply (e.g., 'in', 'exact', 'iexact', etc.).
            check_value (Any): The value to compare against in the condition.
            is_mandatory (bool, optional): Whether the condition is mandatory. Defaults to True.
            skip_if_no_column (bool, optional): Whether to skip the condition if the column does not exist. Defaults to False.
        """
        self.check_key = check_key
        self.check_type = check_type
        self.check_value = check_value
        self.is_mandatory = is_mandatory
        self.skip_if_no_column = skip_if_no_column

    def apply(self, df, safe_str_accessor):
        """
        Applies the condition to the given DataFrame.

        Args:
            df (pd.DataFrame): The DataFrame to apply the condition to.
            safe_str_accessor (function): A function to safely access string methods on DataFrame columns.

        Returns:
            pd.Series: A boolean Series indicating where the condition is met.

        Raises:
            Exception: If an error occurs during the application of the condition.
        """
        try:
            condition_functions = {
                'in': lambda df, key, value: df[key].isin(value),
                'exact': lambda df, key, value: df[key].astype(str) == str(value),
                'iexact': lambda df, key, value: safe_str_accessor(df[key].astype(str), 'lower') == str(value).lower(),
                'notin': lambda df, key, value: ~df[key].isin(value),
                'notequal': lambda df, key, value: df[key].astype(str) != str(value),
                'startswith': lambda df, key, value: safe_str_accessor(df[key].astype(str), 'startswith', str(value)),
                'istartswith': lambda df, key, value: safe_str_accessor(df[key].astype(str), 'lower').str.startswith(str(value).lower()),
                'endswith': lambda df, key, value: safe_str_accessor(df[key].astype(str), 'endswith', str(value)),
                'iendswith': lambda df, key, value: safe_str_accessor(df[key].astype(str), 'lower').str.endswith(str(value).lower()),
                'contains': lambda df, key, value: safe_str_accessor(df[key].astype(str), 'contains', str(value), regex=True),
                'icontains': lambda df, key, value: safe_str_accessor(df[key].astype(str), 'lower').str.contains(str(value).lower(), regex=True),
                'regex': lambda df, key, value: safe_str_accessor(df[key].astype(str), 'match', str(value))
            }

            if self.check_key not in df.columns and self.skip_if_no_column:
                return pd.Series([True] * len(df))
            
            if self.check_type in condition_functions:
                return condition_functions[self.check_type](df, self.check_key, self.check_value)
            else:
                return pd.Series([False] * len(df))
        except Exception as e:
            print(f"Error in Condition.apply: {e}")
            raise e



class TestSubCategoryParameters():
    """
    A class to handle the retrieval and processing of parameters associated with a test sub-category.

    This class provides methods to fetch parameters based on a test sub-category ID, process the parameters,
    and store the results. It also includes functionality to upload processed data to an S3 bucket.
    """

    def get(self, request, test_sub_category_id, file_path=None):
        """
        Retrieve and process parameters for a given test sub-category ID.

        Args:
            request (Request): The request object containing user and other contextual information.
            test_sub_category_id (int): The ID of the test sub-category for which parameters are to be fetched.
            file_path (str, optional): The path where processed files will be stored in S3. Defaults to None.

        Returns:
            dict: A dictionary containing the processed parameters.

        Raises:
            Exception: If the test_sub_category_id is not provided or if no parameters are found for the given ID.
        """
        try:
            self.request = request
            if not test_sub_category_id:
                raise Exception("Please pass test_sub_category_id")
            parameters = Paramters.objects.filter(test_sub_category_id=test_sub_category_id)
            if not parameters:
                raise Exception(f"No Parameters found with test_sub_category_id {test_sub_category_id}")

            result = {}
            current_time = int(time.time())
            for ind, param in enumerate(parameters):
                # param_name = param.name.lower().replace(" ", "_")
                self.combined_columns = self.process_combine_dataframes_input(param.join_keys.get("merge_columns_info", {})) 
                df_list = self.get_dataframes(param)
                self.join_keys = param.join_keys.get("join_info", [])
                df = self.get_final_dataframes(df_list)
                data = self.get_parameter_value(df, param)
                result[param.name] = data
                self.store_result(data = data, param = param)
                self.upload_to_s3(data = data, bucket=f"genaidev", file_name=f"{file_path}/{param.name}.csv")
            return result
        except Exception as e:
            print(f"Error in get method: {e}")
            raise e
    
    def upload_to_s3(self, file_name, bucket, data):
        """
        Upload processed data to an S3 bucket.

        Args:
            file_name (str): The name of the file to be uploaded.
            bucket (str): The name of the S3 bucket.
            data (DataFrame): The data to be uploaded.

        Returns:
            bool: True if the upload is successful, False otherwise.

        Raises:
            Exception: If an error occurs during the upload process.
        """
        try:
            dataframe = pd.DataFrame(data)
            csv_buffer = io.StringIO()
            dataframe.to_csv(csv_buffer, index=False)
            response = s3.put_object(Bucket=bucket, Key=file_name, Body=csv_buffer.getvalue())
        except Exception as e:
            print(f"An error occurred: {e}")
            return False
        return True
        
    def store_result(self, data, param):
        """
        Store the processed result in the database.

        Args:
            data (dict): The processed data to be stored.
            param (Parameter): The parameter object associated with the data.

        Returns:
            bool: True if the data is successfully stored, False otherwise.

        Raises:
            Exception: If an error occurs while storing the data.
        """
        try:
            runtime_params = RuntimeParameterValues(
                data = data,
                parameters = param,
                request_id = self.request.request_id,
                last_updated_by = self.request.user,
                created_by = self.request.user
            )
            runtime_params.save()
            return True
        except Exception as e:
            mesage = f"Error in storing parameter data for parameter {param.name} ::: ERROR: {e}"
            raise Exception(mesage)

    def get_parameter_value(self, df, parameter):
        """
        Extract the required parameter value from the DataFrame based on given conditions.

        Args:
            df (DataFrame): The DataFrame containing the data.
            parameter (Parameter): The parameter object containing conditions and required parameters.

        Returns:
            dict or str: The extracted parameter value(s).

        Raises:
            Exception: If an error occurs during the extraction process.
        """
        try:
            final_mask = self.apply_conditions(df, parameter.conditions)
            df = df[final_mask]
            req_params = parameter.req_params
            df = df[req_params]
            df.replace([np.inf, np.nan, -np.inf], '', inplace=True) 
            data = df.to_dict('records')
            return data if len(data) > 1 else data[0] if len(data) == 1 else ""
        except Exception as e:
            print(f"Error in get_parameter_value: {e}")
            raise e

    def get_file_dataframe(self, bucket, s3_key, file_name):
        """
        Retrieve a DataFrame from an S3 file.

        Args:
            bucket (str): The name of the S3 bucket.
            s3_key (str): The key of the file in the S3 bucket.
            file_name (str): The name of the file.

        Returns:
            DataFrame: The DataFrame created from the file.

        Raises:
            Exception: If an error occurs during the file retrieval or DataFrame creation.
        """
        try:
            file = read_csv_from_s3(bucket, s3_key)
            df = pd.read_csv(file)
            df = self.convert_floats_to_int(df)
            df_renames = {column: f"{file_name}.{column}" for column in df.columns}
            df.rename(columns=df_renames, inplace=True)
            return df
        except Exception as e:
            print(f"Error in get_file_dataframe: {e}")
            raise e
        
    def convert_floats_to_int(self, df):
        """
        Convert float columns in the DataFrame to integers where applicable.

        Args:
            df (DataFrame): The DataFrame to be processed.

        Returns:
            DataFrame: The processed DataFrame.
        """
        for col in df.columns:
            if pd.api.types.is_float_dtype(df[col]):
                df[col].replace([np.inf, -np.inf, np.nan], 0, inplace=True)
                # if all(df[col] == df[col].astype(int)):
                if (df[col] % 1 == 0).all():
                    df[col] = df[col].astype(int)

            df.replace([np.inf, -np.inf, np.nan], '', inplace=True) 
        return df

    def get_dataframes(self, parameter):
        """
        Retrieve DataFrames for the given parameter.

        Args:
            parameter (Parameter): The parameter object containing file information.

        Returns:
            list: A list of dictionaries containing DataFrames and their corresponding file names.

        Raises:
            Exception: If an error occurs during the retrieval process.
        """
        try:
            df_list = []
            files_info = parameter.files_info  # Assuming `files_info` is a list of dicts with keys `bucket`, `s3_key`
            for file_info in files_info:
                file_name = self.get_file_name(file_info['s3_key'])
                df_list.append({
                    "df" : self.get_file_dataframe(file_info['bucket'], file_info['s3_key'], file_name = file_name),
                    "file_name" : file_name,
                })
            return df_list
        except Exception as e:
            print(f"Error in get_dataframes: {e}")
            raise e
        
    def get_file_name(self, s3_key):
        """
        Extract the file name from the S3 key.

        Args:
            s3_key (str): The key of the file in the S3 bucket.

        Returns:
            str: The extracted file name.

        Raises:
            Exception: If an error occurs during the extraction process.
        """
        try:
            return s3_key.split(".")[0].split('/')[-1]
        except Exception as e:
            print(f"Error in get_file_name: {e}")
            raise e
        
    def get_final_dataframes(self, df_list):
        """
        Merge a list of DataFrames into a single DataFrame.

        Args:
            df_list (list): A list of dictionaries containing DataFrames and their corresponding file names.

        Returns:
            DataFrame: The merged DataFrame.

        Raises:
            Exception: If an error occurs during the merging process.
        """
        try:
            if len(df_list) == 0:
                return pd.DataFrame([])
            df, file_name = df_list.pop(0).values()
            for next_df_details in df_list:
                df_2 = next_df_details['df']
                file_name2 = next_df_details['file_name']
                df = self.join_dataframes(df, df_2, file_name, file_name2)
            return df
        except Exception as e:
            print(f"Error in get_final_dataframes: {e}")
            raise e

    def join_dataframes(self, df_1, df_2, file1_name, file2_name, join_type="inner"):
        """
        Join two DataFrames based on specified keys.

        Args:
            df_1 (DataFrame): The first DataFrame to be joined.
            df_2 (DataFrame): The second DataFrame to be joined.
            file1_name (str): The name of the first file.
            file2_name (str): The name of the second file.
            join_type (str, optional): The type of join to be performed. Defaults to "inner".

        Returns:
            DataFrame: The joined DataFrame.

        Raises:
            Exception: If an error occurs during the join process.
        """
        try:
            if df_1.empty or df_2.empty:
                raise Exception("One of the DataFrames is empty and cannot be joined")
            condition = self.join_keys.pop(0)

            if (self.combined_columns.get(file1_name, None)):
                df_1 = self.merge_columns(df_1, self.combined_columns[file1_name])
            if (self.combined_columns.get(file2_name,None)):
                df_2 = self.merge_columns(df_2, self.combined_columns[file2_name])

            if "==" in condition:
                key1, key2 = condition.split("==")
            elif '=' in condition:
                key1, key2 = condition.split("=")
            else:
                message = f"unable to split the condition to join csv files [{file1_name}, {file2_name}] with condition '{condition}'"
                raise Exception(message)

            key1, key2 = key1.strip(), key2.strip()
            
            try:
                df = df_1.merge(df_2, right_on=key1, left_on=key2,  how=join_type)
            except Exception as e:
                try:
                    df = df_1.merge(df_2, left_on=key1, right_on=key2, how=join_type)
                except Exception as e:
                    raise e
            return df
        except Exception as e:
            print(f"Error in join_dataframes: {e}")
            raise e
        
    def process_combine_dataframes_input(self, data={} ):
        """
        Process the input data for combining DataFrames.

        Args:
            data (dict, optional): The input data containing file names and their corresponding column data. Defaults to {}.

        Returns:
            dict: The processed data.
        """
        _data = {}
        for file_name, file_data in data.items():
            file_name = file_name.split('.')[0]
            _data[file_name] = {}
            for column, column_data in file_data.items():
                new_column_name = f"{file_name}.{column}"
                _data[file_name][new_column_name] = column_data
        return _data

    def merge_columns(self, df, combine_columns):
        """
        Merge specified columns in the DataFrame.

        Args:
            df (DataFrame): The DataFrame to be processed.
            combine_columns (dict): The dictionary containing columns to be merged and their corresponding merge information.

        Returns:
            DataFrame: The processed DataFrame.
        """

        for new_col, merge_info in combine_columns.items():
            cols_to_merge = merge_info['columns_to_merge']
            seperator = merge_info.get('seperator', '-')
            if seperator in ['or', 'OR', 'Or', 'oR']:
                df[new_col] = df[cols_to_merge[0]]
                for col in cols_to_merge[1:]:
                    df[new_col] = df[new_col].fillna(df[col])
            else:
                df[new_col] = df[cols_to_merge[0]].astype(str)
                for col in cols_to_merge[1:]:
                    df[new_col] += seperator + df[col].astype(str)
        return df
        
    def resolve_column_names(self, df, check_keys):
        """
        Resolve column names in the DataFrame based on the given keys.

        Args:
            df (DataFrame): The DataFrame to be processed.
            check_keys (list or str): The keys to be resolved.

        Returns:
            list or str: The resolved column names.

        Raises:
            Exception: If an error occurs during the resolution process.
        """
        try:
            if isinstance(check_keys, list):
                columns = []
                for check_key in check_keys:
                    columns.append(self.get_column_name(df, check_key))
                return columns
            return self.get_column_name(df, check_keys)
        except Exception as e:
            print(f"Error in resolve_column_names: {e}")
            raise e

    def get_column_name(self, df, check_key):
        """
        Retrieve the column name in the DataFrame based on the given key.

        Args:
            df (DataFrame): The DataFrame to be processed.
            check_key (str): The key to be resolved.

        Returns:
            str: The resolved column name.

        Raises:
            Exception: If an error occurs during the retrieval process.
        """
        try:
            if check_key in df.columns:
                return check_key
            for col in df.columns:
                if col.endswith(f".{check_key}"):
                    return col
            return check_key
        except Exception as e:
            print(f"Error in get_column_name: {e}")
            raise e

    def safe_str_accessor(self, series, method, *args, **kwargs):
        """
        Safely apply a string method to a pandas Series.

        Args:
            series (Series): The pandas Series to which the method will be applied.
            method (str): The name of the string method to be applied.
            *args: Positional arguments to be passed to the method.
            **kwargs: Keyword arguments to be passed to the method.

        Returns:
            Series: The Series after applying the method.

        Raises:
            Exception: If an error occurs during the application of the method.
        """
        try:
            return getattr(series.astype(str).str, method)(*args, **kwargs)
        except Exception as e:
            print(f"Error in safe_str_accessor: {e}")
            raise e

    def apply_conditions(self, df, conditions_dict):
        """
        Apply conditions to the DataFrame to filter rows.

        Args:
            df (DataFrame): The DataFrame to be processed.
            conditions_dict (dict): The dictionary containing conditions to be applied.

        Returns:
            Series: A boolean Series indicating which rows satisfy the conditions.

        Raises:
            Exception: If an error occurs during the application of conditions.
        """
        try:
            conditions = self.parse_conditions(conditions_dict['conditions'])
            final_mask = self.evaluate_conditions(df, conditions)
            return final_mask
        except Exception as e:
            print(f"Error in apply_conditions: {e}")
            raise e

    def parse_conditions(self, conditions_dict):
        """
        Parse the conditions dictionary into a list of Condition objects.

        Args:
            conditions_dict (dict): The dictionary containing conditions to be parsed.

        Returns:
            list: A list of Condition objects.

        Raises:
            Exception: If an error occurs during the parsing process.
        """
        try:
            conditions = []
            for cond in conditions_dict.get('and', []):
                if 'conditions' in cond:
                    sub_conditions = self.parse_conditions(cond['conditions'])
                    conditions.append((list(cond['conditions'].keys())[0], sub_conditions))
                else:
                    conditions.append(Condition(cond['check_key'], cond['check_type'], cond['check_value'], cond.get('is_mandatory', True), cond.get('skip_if_no_column', False)))

            for cond in conditions_dict.get('or', []):
                if 'conditions' in cond:
                    sub_conditions = self.parse_conditions(cond['conditions'])
                    conditions.append((list(cond['conditions'].keys())[0], sub_conditions))
                else:
                    conditions.append(Condition(cond['check_key'], cond['check_type'], cond['check_value'], cond.get('is_mandatory', True), cond.get('skip_if_no_column', False)))

            return conditions
        except Exception as e:
            print(f"Error in parse_conditions: {e}")
            raise e

    def evaluate_conditions(self, df, conditions):
        """
        Evaluate the parsed conditions on the DataFrame.

        Args:
            df (DataFrame): The DataFrame to be processed.
            conditions (list): The list of Condition objects to be evaluated.

        Returns:
            Series: A boolean Series indicating which rows satisfy the conditions.

        Raises:
            Exception: If an error occurs during the evaluation process.
        """
        try:
            if not conditions:
                return pd.Series([True] * len(df))

            results = []
            for condition in conditions:
                if isinstance(condition, tuple):
                    cond_type, conds = condition
                    if cond_type == 'and':
                        masks = [cond.apply(df, self.safe_str_accessor) for cond in conds]
                        results.append(pd.concat(masks, axis=1).all(axis=1))
                    elif cond_type == 'or':
                        masks = [cond.apply(df, self.safe_str_accessor) for cond in conds]
                        results.append(pd.concat(masks, axis=1).any(axis=1))
                else:
                    results.append(condition.apply(df, self.safe_str_accessor))

            if len(results) == 1:
                return results[0]
            else:
                return pd.concat(results, axis=1).all(axis=1)
        except Exception as e:
            print(f"Error in evaluate_conditions: {e}")
            raise e

