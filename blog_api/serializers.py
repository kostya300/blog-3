from rest_framework import serializers
from blog.models import Post


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        (
            "id",
            "author",
            "title",
            "body",
            "created",
            "status",
            "slug",
        )
        model = Post
