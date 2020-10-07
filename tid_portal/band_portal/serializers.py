from rest_framework import serializers
from .models import *


class SongSerializer(serializers.Serializer):

    artist = serializers.CharField(max_length=100)
    name = serializers.CharField(max_length = 100)
    live_position = serializers.IntegerField()
    tempo = serializers.IntegerField()
    id = serializers.IntegerField(read_only=True)

    def create(self, validated_data):

        song_obj = Song(**validated_data)
        song_obj.save()
        return song_obj


    def update(self, instance, validated_data):

        instance.artist = validated_data["artist"]
        instance.name = validated_data["name"]
        instance.live_position = validated_data["live_position"]
        instance.tempo = validated_data["tempo"]
        instance.save()
        return instance

