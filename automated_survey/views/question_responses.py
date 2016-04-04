from django.views.generic import View
from django.core.urlresolvers import reverse
from django.shortcuts import redirect
from django.http import HttpResponse
from twilio import twiml

from automated_survey.models import Survey, QuestionResponse, Question
from automated_survey.views.common import parameters_for_survey_url


class QuestionResponseView(View):
    http_method_names = ['post']

    def post(self, request, survey_id, question_id):
        question = Question.objects.get(id=question_id)
        response = QuestionResponse.from_twilio_request(request)
        response.question = question
        response.save()
        return self._redirect_to_next_question(question)

    def _redirect_to_next_question(self, question):
        next_question = self._next_question(question)
        if not next_question:
            return self._goodbye_message()

        url_parameters = parameters_for_survey_url(
            next_question.survey_id, next_question.id)
        next_question_url = reverse('question', kwargs=url_parameters)

        see_other = redirect(next_question_url)
        see_other.status_code = 303
        see_other.reason_phrase = 'See Other'

        return see_other

    def _next_question(self, question):
        survey = Survey.objects.get(id=question.survey_id)

        next_questions = \
            survey.question_set.order_by('id').filter(id__gt=question.id)

        return next_questions[0] if next_questions else None

    def _goodbye_message(self):
        text_response = twiml.Response()
        text_response.say('That was the last question')
        text_response.say('Thank you for taking this survey')
        text_response.say('Good-bye')
        text_response.hangup()

        return HttpResponse(text_response)
