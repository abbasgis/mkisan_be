import logging
import os
import traceback
import uuid


class PipelinesUtils:
    @classmethod
    def value_check(cls, field_value, values):
        if field_value not in values:
            raise ValueError('Unknown method')

    @classmethod
    def make_dirs(cls, file_path_name: str):
        file_dir, file_name = cls.separate_file_path_name(file_path_name)
        os.makedirs(file_dir, exist_ok=True)

    @classmethod
    def separate_file_path_name(cls, file_path_name: str):
        file_dir = os.path.dirname(file_path_name)
        file_name = os.path.basename(file_path_name)
        return file_dir, file_name

    @classmethod
    def get_file_name_extension(cls, file_name: str) -> (str, str):
        split = file_name.split(".")
        if len(split) == 2:
            return split[0], split[1]
        return file_name, None

    @classmethod
    def get_uuid(cls):
        return str(uuid.uuid1().hex)


class DataLogger:
    @classmethod
    def log_view_error_message(cls, e, request=None, redirect_path=None):
        error_message = str(e)
        cls.log_error_message(e)
        if request:
            if redirect_path is None:
                redirect_path = request.META.get('HTTP_REFERER', '')
                if redirect_path == '':
                    redirect_path = "/"
            return redirect_path

        # response.write(error_message)

    @classmethod
    def log_error_message(cls, e, message_type="error", user_id=None):
        error_message = str(e)
        # logger = logging.getLogger()

        logging.error(traceback.format_exc())
        print("error_message: ", error_message)
        # log_data = get_log_data()
        #
        # ActivityLog().log_message(log_data,LogType.Err)
        return error_message  # , act_log.id
