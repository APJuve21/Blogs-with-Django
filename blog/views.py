from django.shortcuts import get_object_or_404
from django.db.models import Q
from rest_framework import generics
from rest_framework.response import Response
from blog.models import Quiz, QuizTaker, UsersAnswer
from blog.serializers import QuizListSerializer, QuizDetailSerializer

from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.views.generic import (
	ListView, 
	DetailView,
	CreateView,
	UpdateView,
	DeleteView
	)
from .models import Post

# Create your views here.
from django.http import HttpResponse

def home(request):
	#pass posts into template
	context = {
		'posts': Post.objects.all()
	}
	return render(request, 'blog/home.html', context) #render takes request object and template name we want to render (indicate subdirectory). Third argument is dictionary context

class PostListView(ListView):
	model = Post
	template_name = 'blog/home.html' #<app>/<model>_<viewtype>.html
	context_object_name = 'posts'
	ordering = ['-date_posted'] #latest post first

class PostDetailView(DetailView):
	model = Post

class PostCreateView(LoginRequiredMixin, CreateView):
	model = Post
	fields = ['title', 'content']

	def form_valid(self, form):
		form.instance.author = self.request.user
		return super().form_valid(form) #override to allow post to set author

class PostUpdateView(LoginRequiredMixin, UserPassesTestMixin, UpdateView):
	model = Post
	fields = ['title', 'content']

	def form_valid(self, form):
		form.instance.author = self.request.user
		return super().form_valid(form) #override to allow post to set author

	def test_func(self):
		post = self.get_object()
		if self.request.user == post.author:
			return True
		return False #makes sure author of another account cannot update someone else's post

class PostDeleteView(LoginRequiredMixin, UserPassesTestMixin, DeleteView):
	model = Post
	success_url = '/'

	def test_func(self):
		post = self.get_object()
		if self.request.user == post.author:
			return True
		return False

def about(request):
	return render(request, 'blog/about.html', {'title': 'About'}) #still returns HTTP Response


class QuizListAPI(generics.ListAPIView):

	serializer_class = QuizListSerializer

	def get_queryset(self, *args, **kwargs):
		queryset = Quiz.objects.filter(roll_out = True)
		query = self.request.GET.get("q")

		if query:
			queryset = queryset.filter(
				Q(name__icontains=query) |
				Q(description__icontains=query)
			).distinct()

		return queryset


class QuizDetailAPI(generics.RetrieveAPIView):
	serializer_class = QuizDetailSerializer

	def get(self, *args, **kwargs):
		slug = self.kwargs["slug"]
		quiz = get_object_or_404(Quiz, slug=slug)
		last_question = None
		obj, created = QuizTaker.objects.get_or_create(user=self.request.user, quiz=quiz)
		if created:
			for question in Question.objects.filter(quiz=quiz):
				UsersAnswer.objects.create(quiz_taker=obj, question=question)
		else:
			last_question = UsersAnswer.objects.filter(quiz_taker=obj, answer__isnull=False)
			if last_question.count() > 0:
				last_question = last_question.last().question.id
			else:
				last_question = None

		return Response({'quiz': self.get_serializer(quiz, context={'request': self.request}).data, 'last_question_id': last_question})

