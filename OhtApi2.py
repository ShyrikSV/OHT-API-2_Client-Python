 # -*- coding: utf-8 -*-

from collections import namedtuple
import json
import requests
import requests.exceptions

class OhtApi:

    _apiUrl  = {"account-details": "/account/",
                "create-file-resource": "/resources/file",
                "get-resource": "/resources/{0}",
                "download-resource": "/resources/{0}/download",
                "quote": "/tools/quote",
                "word-count": "/tools/wordcount",
                "new-translation-project": "/projects/translation",
                "new-proofreading-project-single": "/projects/proof-general",
                "new-proofreading-project-advanced": "/projects/proof-translated",
                "new-transcription-project": "/projects/transcription",
                "project-details": "/projects/{0}",
                "cancel-project": "/projects/{0}",
                "project-comments": "/projects/{0}/comments",
                "new-comment": "/projects/{0}/comments",
                "retrieve-project-ratings": "/projects/{0}/rating",
                "post-project-ratings": "/projects/{0}/rating",
                "machine-translate": "/mt/translate/text",
                "machine-detect-lang": "/mt/detect/text",
                "discover-langs": "/discover/languages",
                "discover-langs_pairs": "/discover/language_pairs",
                "supported-expertises": "/discover/expertise"
                }

    def __init__(self, public_key, private_key, sandbox=False, time_out=10):
        """
        time_out param use only for check URL availability
        """
        self.__askTimeOut = time_out
        self.__publicKey = public_key
        self.__privateKey = private_key
        self.__sandbox = sandbox

        self.__baseUrl = "http://www.onehourtranslation.com/api/2"
        self.__sandboxUrl = "http://sandbox.onehourtranslation.com/api/2"

        self._renew_work_url()

    def _renew_work_url(self):
        """
        Check availability self.__workUrl
        :return: Boolean

        """
        self.__workUrl = self.__sandboxUrl if self.__sandbox else self.__baseUrl

        try:
            rez = requests.head(self.__workUrl, timeout=self.__askTimeOut).status_code == requests.codes.ok
        except requests.exceptions.MissingSchema:
            if self.__sandbox:
                self.__sandboxUrl = "https://" + self.__sandboxUrl
            else:
                self.__baseUrl = "https://" + self.__baseUrl

            rez = self._renew_work_url()

        return rez

    def _param_injection_helper(self, target, custom=None, **kwargs):

        for key, val in kwargs.items():
            target[key] = val

        if custom and type(custom).__name__ == "list" and len(custom):
            index = 0
            for item in custom:
                target["custom{0}".format(index)] = item
                index += 1
                if index >= 10:
                    break

    def _json_to_object_hook(self, data):
        d = {}
        for key in data.keys():
            if not key.isidentifier():
                d[key] = data[key]
        return d if d else namedtuple("oht_response", data.keys())(*data.values())

    def json_to_ntuple(self, data):
        """
        :param data: response json from OHT server
        :return namedtuple
        :raise ValueError if data contain invalid json string

        """
        return json.loads(data, object_hook=self._json_to_object_hook)

    def set_base_url(self, new_url):
        """
        Set new URL for product. If URL come without 'http[s]:\\' prefix - it will be add.
        :param new_url:
        :return {Boolean} True if ok, False if server return non 200 code
        :raise requests.exceptions.ConnectionError if URl is unavailable

        """
        if self.__baseUrl != new_url:
            self.__baseUrl = new_url
            return self._renew_work_url()
        else:
            return True

    def base_url(self):
        return self.__baseUrl

    def set_sandbox_url(self, new_url):
        """
        Set new URL for sandbox. If URL come without 'http[s]:\\' prefix - it will be add.
        :param new_url:
        :return {Boolean} True if ok, False if server return non 200 code
        :raise requests.exceptions.ConnectionError if URl is unavailable

        """
        if self.__sandboxUrl != new_url:
            self.__sandboxUrl = new_url
            return self._renew_work_url()
        else:
            return True

    def sandbox_url(self):
        return self.__sandboxUrl

    def account_details(self):
        """
        Fetch basic account details and credits balance
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK. More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> namedtuple with fields:
                account_id: {Integer} -> Unique account id in OHT
                account_username: {String} -> OHT username
                credits: {Integer} -> Currently available credits balance
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["account-details"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def create_file_resource(self, upload=None, file_name="", file_mime="", file_content=""):
        """
        Create a new file entity from supported formats.
        After the resource entity is created, it can be used on job requests such as translation, proofreading, etc.
        More info: https://www.onehourtranslation.com/translation/api-documentation-v2/content-formats
        :param upload: {String} -> (optional, see file_content) Path to file, witch content will be upload (submitted via multipart/form-data request)
        :param file_name: {String} -> (optional) Replace the original file's name on One Hour Translation
        :param file_mime: {String} -> (optional) Replace the default mime value for the file
        :param file_content: {String} -> Content of the new file, works only with "file_name" not empty. If used, actual upload is skipped.
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: {List} -> list of uuid uploaded file
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["create-file-resource"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "file_name": file_name,
                  "file_mime": file_mime,
                  "file_content": file_content}
        if upload:
            file = {"file": open(upload, 'rb')}
            return self.json_to_ntuple(requests.post(api, params=params, files=file).text)
        else:
            return self.json_to_ntuple(requests.post(api, params=params).text)

    def get_resource(self, resource_uuid, project_id=-1, fetch=""):
        """
        Provides information regarding a specific resource
        :param resource_uuid: {String}
        :param project_id: {Integer} -> (optional) Project ID, needed when requesting a resource that was uploaded by another user - e.g. as a project’s translation
        :param fetch: {String} -> (optional) possible values: false - (default) do not fetch content; base64 - fetch content, base64 encoded
        :return: namedtuple with fields:
            status: status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: namedtuple with fields:
                type: {String} -> text|file
                length: {Integer} -> file size in bytes
                file_name: {String} -> File name (only for files)
                file_mime: {String} -> File mime (only for files)
                download_url: {String} -> URL to download as file (currently str link to the API call “Download resource”...)
                content: {String} -> base64 encoded (only if fetch=”base64”)
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["get-resource"].format(resource_uuid)
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey}
        if project_id != -1:
            params["project_id"] = project_id

        if fetch:
            params["fetch"] = fetch

        return self.json_to_ntuple(requests.get(api, params=params).text)

    def download_resource(self, resource_uuid, path_to_save="", chunk_size=128, project_id=-1):
        """
        Download resource
        :param resource_uuid: {String} -> resource uuid
        :param path_to_save: {String} -> (optional) path to file to save resource
        :param chunk_size: {Integer} -> (optional) chunk size for fetch content
        :param project_id:  {Integer} -> (optional) (optional) Project ID, needed when requesting a resource that was uploaded by another user - e.g. as a project’s translation
        :return: depends of 'path_to_save' option:
            if not specified: function return downloaded text
            if specified: function return file path on success, otherwise empty string

        """
        api = self.__workUrl + self._apiUrl["download-resource"].format(resource_uuid)
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey}
        if project_id != -1:
            params["project_id"] = project_id

        if not path_to_save:
            return requests.get(api, params=params).text
        else:
            req = requests.get(api, params=params, stream=True)
            if req.status_code == requests.codes.ok:
                with open(path_to_save, "wb") as file:
                    for chunk in req.iter_content(chunk_size):
                        file.write(chunk)
                return path_to_save
            return ""

    def quote(self, resources, source_lang, target_lang, wordcount=0, service="", expertise="", proofreading="", currency=""):
        """
        Get the summary of an order
        :param resources: {List} -> list of resource_uuid
        :param wordcount: {Integer} -> word count, if specified - it will override real word count and [resources] block will be disappear. If pass 0 - [resources] block will be
            contain real word count for each resource.
        :param source_lang: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param target_lang: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param service: {String} -> translation | proofreading | transproof | transcription ( translation by default)
        :param expertise: {String} -> expertise codes, see function expertises and https://www.onehourtranslation.com/translation/api-documentation-v2/expertise-codes
        :param proofreading: {String} -> 0 | 1
        :param currency: {String} -> USD | EUR
        :return: namedtuple with fields:
            status: status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: namedtuple with fields:
                resources: {List} -> list of namedtuple with fields:
                    wordcount: {Integer} -> word count of the resource
                    credits: {String} -> credits worth of the resource
                    resource: {String} -> UUID of the resource in list
                    price: {Integer} -> price of the resource
                total: namedtuple with fields:
                    wordcount: {Integer} -> total words count
                    credits: {String} -> sum of credits to charge
                    net_price: {Integer} -> price in selected currency, based on credits and discounts
                    transaction_fee: {Integer} -> price in selected currency, based on fee from payment vendors
                    price: {Integer} -> total price in selected currency, based on net price and transaction fee.
                currency: {String} -> USD | EUR
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["quote"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "resources": ",".join(resources),
                  "wordcount": wordcount,
                  "source_language": source_lang,
                  "target_language": target_lang}
        self._param_injection_helper(params, service=service, expertise=expertise, proofreading=proofreading, currency=currency)
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def word_count(self, resources):
        """
        Get the word count of provided resources
        :param resources: {List} -> list of resource_uuid
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> namedtuple with fields:
                resources: {List} -> list of namedtuple with asked resource_uuid with fields:
                    resource: {String} -> resource_uuid
                    wordcount: {Integer} -> wordcount in resource_uuid
                total: {Integer} -> total words count in asked list of resource_uuid
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["word-count"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "resources": ",".join(resources)}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def create_translation_project(self, source_lang, target_lang, sources, word_count=0, notes="", expertise="", callback_url="", custom=None, name=""):
        """
        Open a new translation project with One Hour Translation
        :param source_lang: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param target_lang: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param sources: {List} -> list of Resource UUIDs
        :param word_count: {Integer} -> (optional) If empty use automatic counting
        :param notes: {String} -> (optional) Text note that will be shown to translator regarding the newly project
        :param expertise: {String} -> (optional) see https://www.onehourtranslation.com/translation/api-documentation-v2/expertise-codes
        :param callback_url: {String} -> (optional) see https://www.onehourtranslation.com/translation/api-documentation-v2/callbacks
        :param custom: {List} -> (optional, 0..9 items) ???
        :param name: {String} -> (optional) Name your project. If empty, your project will be named automatically.
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> namedtuple with fields:
                project_id: {Integer} -> unique id of the newly project created
                wordcount: {Integer} -> total word count of the newly project
                credits: {Integer} -> total credit worth of the newly project
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["new-translation-project"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "source_language": source_lang,
                  "target_language": target_lang,
                  "sources": ",".join(sources)}
        self._param_injection_helper(params, custom=custom, wordCount=word_count, notes=notes, expertise=expertise, callbackUrl=callback_url, name=name)
        return self.json_to_ntuple(requests.post(api, params=params).text)

    def create_proof_reading_project(self, source_lang, sources, word_count=0, notes="", expertise="", callback_url="", custom=None, name=""):
        """
        Create new proofreading project, same language
        :param source_lang: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param sources: {List} -> list of Resource UUIDs
        :param word_count: {Integer} -> (optional) If empty use automatic counting
        :param notes: {String} -> (optional) Text note that will be shown to translator regarding the newly project
        :param expertise: {String} -> (optional) see https://www.onehourtranslation.com/translation/api-documentation-v2/expertise-codes
        :param callback_url: {String} -> (optional) see https://www.onehourtranslation.com/translation/api-documentation-v2/callbacks
        :param custom: {List} -> (optional, 0..9 items) ???
        :param name: {String} -> (optional) Name your project. If empty, your project name will be blank
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> namedtuple with fields:
                project_id: {Integer} -> unique id of the newly project created
                wordcount: {Integer} -> total word count of the newly project
                credits: {Integer} -> total credit worth of the newly project
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["new-proofreading-project-single"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "source_language": source_lang,
                  "sources": ",".join(sources)}
        self._param_injection_helper(params, custom=custom, wordCount=word_count, notes=notes, expertise=expertise, callbackUrl=callback_url, name=name)
        return self.json_to_ntuple(requests.post(api, params=params).text)

    def create_proof_translated_project(self, source_lang, target_lang, sources, translations, word_count=0, notes="", expertise="", callback_url="", custom=None, name=""):
        """
        Create new proofreading project, Providing source and translation
        :param source_lang: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param target_lang: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param sources: {List} -> list of Resource UUIDs
        :param translations: {List} -> list of Resource UUIDs
        :param word_count: {Integer} -> (optional) If empty use automatic counting
        :param notes: {String} -> (optional) Text note that will be shown to translator regarding the newly project
        :param expertise: {String} -> (optional) see https://www.onehourtranslation.com/translation/api-documentation-v2/expertise-codes
        :param callback_url: {String} -> (optional) see https://www.onehourtranslation.com/translation/api-documentation-v2/callbacks
        :param custom: {List} -> (optional, 0..9 items) ???
        :param name: {String} -> (optional) Name your project. If empty, your project name will be blank
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> namedtuple with fields:
                project_id: {Integer} -> unique id of the newly project created
                wordcount: {Integer} -> total word count of the newly project
                credits: {Integer} -> total credit worth of the newly project
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["new-proofreading-project-advanced"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "source_language": source_lang,
                  "target_language": target_lang,
                  "sources": ",".join(sources),
                  "translations": ",".join(translations)}
        self._param_injection_helper(params, custom=custom, wordCount=word_count, notes=notes, expertise=expertise, callbackUrl=callback_url, name=name)
        print(requests.post(api, params=params).url)
        return self.json_to_ntuple(requests.post(api, params=params).text)

    def create_transcription_project(self, source_lang, sources, length=0, notes="", callback_url="", custom=None, name=""):
        """
        Create a transcription project at One Hour Translation
        :param source_lang: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param sources: {List of Strings} -> list of Resource UUIDs
        :param length: {Integer} -> (optional) Integer of seconds, if empty use automatic counting
        :param notes: {String} -> (optional) Text note that will be shown to translator regarding the newly project
        :param callback_url: {String} -> (optional) see https://www.onehourtranslation.com/translation/api-documentation-v2/callbacks
        :param custom: {List} -> (optional, 0..9 items) ???
        :param name: {String} -> (optional) Name your project. If empty, your project name will be blank
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> namedtuple with fields:
                project_id: {Integer} -> unique id of the newly project created
                length: {Integer} -> total length (in seconds) of the newly transcription project
                credits: {Integer} -> total credit worth of the newly project
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["new-transcription-project"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "source_language": source_lang,
                  "sources": ",".join(sources)}
        self._param_injection_helper(params, custom=custom, length=length, notes=notes, callbackUrl=callback_url, name=name)
        return self.json_to_ntuple(requests.post(api, params=params).text)

    def project_detail(self, project_id):
        """
        Get a detailed specification of a project
        :param project_id: {Integer} -> project id
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: namedtuple with fields:
                project_id: {String} -> the unique id of the requested project
                project_type: {String} -> Translation | Expert Translation | Proofreading | Transcription | Translation + Proofreading
                project_status: {String} -> Pending | in_progress | submitted | signed | completed | canceled
                                            pending - project submitted to OHT, but professional worker (translator/proofreader) did not start working yet
                                            in_progress - worker started working on this project
                                            submitted - the worker uploaded the first target resource to the project. This does not mean that the project is completed.
                                            signed - the worker declared (with his signature) that he finished working on this project and all resources have been uploaded.
                                            completed - final state of the project, after which we cannot guarantee fixes or corrections. This state is automatically enforced after 4 days of inactivity on the project.
                project_status_code: {String} ->
                source_language: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
                target_language: {String} -> language codes, see https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
                resources: namedtuple with fields
                    translations: {String}
                    proofs: {String}
                    transcriptions: {List} -> resources uuid
                    sources: {List} -> resources uuid
                wordcount | length : {Integer} -> length - in seconds (transcription projects only);
                custom: {String} ->
                resource_binding: {Dict} -> key {String}: resource uuid, value {List}: resources uuid
                linguist_uuid: {String} ->
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["project-details"].format(project_id)
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def cancel_project(self, project_id):
        """
        Prevent a project from being worked on by a linguist
        Constraints: Available only before actual translation starts
        :param project_id: {Integer} -> project id to cancel
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: {List} -> empty
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["cancel-project"].format(project_id)
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey}

        return self.json_to_ntuple(requests.request('delete', api, params=params).text)

    def project_comments(self, project_id):
        """
        Receive comments posted on the project page
        :param project_id: {Integer} -> project id
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: {List} -> list of comments with fields:
                id: {Integer} -> unique id of the comment
                date: {String} -> The date the comment was created
                commenter_name: {String} -> Short representation of the user’s name
                commenter_role: {String} -> admin | customer | provider | potential-provider
                                            admin - OHT support team
                                            provider - The translator / proofreader / transcriber that is assigned to the project
                                            potential-provider - A translator / proofreader / transcriber that was allowed to view the project before it was assigned
                comment_content: {String} -> text content
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["project-comments"].format(project_id)
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def post_comment(self, project_id, text):
        """
        Post a new comment to the project page
        :param project_id: {Integer} -> project id
        :param text: {String} -> test to post in comment
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: {List} -> empty
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["new-comment"].format(project_id)
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "content": text}

        return self.json_to_ntuple(requests.post(api, params=params).text)

    def project_ratings(self, project_id):
        """
        Get the rating for the quality of the translation and service
        :param project_id: {Integer} -> project id
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: {List} -> list of rates - namedtuple with fields:
                type: {String} -> Customer|Service
                rate: {String} -> Rating of project (1 - being the lowest; 10 - being the highest)
                remarks: {String} -> Remark left with the rating
                date: {String} -> Date and time of last update to the rating
                status_approved: {String} -> ?
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["retrieve-project-ratings"].format(project_id)
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "project_id": project_id}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def post_project_ratings(self, project_id, comment_type, rate, remarks=""):
        """
        Post a rating for the quality of the translation and service
        :param project_id: {Integer} -> project id
        :param comment_type: {String} -> Customer|Service
        :param rate: {Integer} -> Rating of project (1 - being the lowest; 10 - being the highest)
        :param remarks: {String} -> (optional) Remark left with the rating
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: {List} -> empty
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["post-project-ratings"].format(project_id)
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "project_id": project_id,
                  "type": comment_type,
                  "rate": rate}

        if(remarks):
            params["remarks"] = remarks

        return self.json_to_ntuple(requests.post(api, params=params).text)

    def machine_translate(self, from_lang, to_lang, text):
        """
        Translate via machine translation
        :param from_lang: language code, More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
        :param to_lang: language code, see :param from_lang
        :param text: Text for translation
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: result namedtuple with field:
                TranslatedText: {String} -> The translated content in the original format
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["machine-translate"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "source_language": from_lang,
                  "target_language": to_lang,
                  "source_content": text}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def machine_detect_lang(self, text):
        """
        Detect language via machine translation
        :param text: {String} -> Text for translation
        :return:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results: namedtuple with field:
                language: {String} -> detected language
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["machine-detect-lang"]
        params = {"public_key": self.__publicKey,
                  "secret_key": self.__privateKey,
                  "source_content": text}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def supported_languages(self):
        """
        Discover which languages are supported by OHT
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> {List} -> list of supported languages pairs, namedtuple with fields:
                code: {String} -> code of language, more info: https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
                name: {String} -> human-readable name of language
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["discover-langs"]
        params = {"public_key": self.__publicKey}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def supported_language_pairs(self):
        """
        Discover which language pairs are supported by OHT
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> {List} -> list of supported language pairs, namedtuple with fields:
                source: namedtuple represented source language with fields:
                    code: {String} -> code of language, more info: https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
                    name: {String} -> human-readable name of language
                targets: {List} -> list of namedtuple for supported targets languages
                    code: {String} -> code of language
                    availability: {String} -> available values: [high, medium, low]:
                        high = work is expected to start within an hour on business hours
                        medium = work is expected to start within one day
                        low = work is expected to start within a week
                  name: {String} -> human-readable name of language
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["discover-langs_pairs"]
        params = {"public_key": self.__publicKey}
        return self.json_to_ntuple(requests.get(api, params=params).text)

    def expertises(self, source_lang="", target_lang=""):
        """
        :param source_lang: {String} -> optional, mandatory if target_language is specified. See https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :param target_lang: {String} -> optional, mandatory if source_language is specified. See https://www.onehourtranslation.com/translation/api-documentation-v2/language-codes
        :return: namedtuple with fields:
            status -> status with fields:
                code: {Integer} -> request status code, 0 for OK.  More info: https://www.onehourtranslation.com/translation/api-documentation-v2/general-instructions#status-and-error-codes
                msg: {String} -> request status message, "ok" for OK
            results -> {List} -> list of supported expertises, ordered by name field (A->Z). Namedtuple with fields:
                expertise_name: {String} -> see https://www.onehourtranslation.com/translation/api-documentation-v2/callbacks
                expertise_code: {String} -> see https://www.onehourtranslation.com/translation/api-documentation-v2/callbacks
            errors: {List} -> list of errors

        """
        api = self.__workUrl + self._apiUrl["supported-expertises"]
        params = {"public_key": self.__publicKey,
                  "source_language": source_lang,
                  "target_language": target_lang}
        return self.json_to_ntuple(requests.get(api, params=params).text)
