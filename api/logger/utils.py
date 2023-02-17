import logging
import traceback

from django.contrib import messages


class DataLogger:
    @classmethod
    def log_view_error_message(cls, e, request=None, redirect_path=None):
        error_message = str(e)
        cls.log_error_message(e)
        if request:
            messages.add_message(request, messages.ERROR, error_message)
            if redirect_path is None:
                redirect_path = request.META.get('HTTP_REFERER', '')
                if redirect_path == '':
                    redirect_path = "/"
            return redirect_path

        # response.write(error_message)

    @classmethod
    def log_error_message(cls, e, message_type="error", user_id=None):
        error_message = str(e)
        logger = logging.getLogger()

        logger.error(traceback.format_exc())
        # log_data = get_log_data()
        #
        # ActivityLog().log_message(log_data,LogType.Err)
        return error_message  # , act_log.id
