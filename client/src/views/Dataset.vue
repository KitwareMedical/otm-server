<template>
  <div>
    <v-progress-linear v-if="loading" indeterminate />
    <template v-else>
      <div class="title">{{ dataset.name }}</div>
      <div class="body-0 my-2">{{ dataset.description }}</div>
    </template>
    <v-tabs>
      <v-tab :to="`/dataset/${datasetId}/images`">Images</v-tab>
      <v-tab :to="`/dataset/${datasetId}/upload`">Upload</v-tab>
      <v-tab :to="`/dataset/${datasetId}/uploads`">Pending Uploads</v-tab>
    </v-tabs>
    <router-view></router-view>
  </div>
</template>

<script>
export default {
  inject: ['girderRest'],
  props: {
    datasetId: {
      required: true,
      type: String,
    },
  },
  data() {
    return {
      dataset: null,
      loading: true,
    };
  },
  async mounted() {
    this.loading = true;
    const resp = await this.girderRest.get(`datasets/${this.datasetId}`);
    this.dataset = resp.data;
    this.loading = false;
  }
};
</script>
