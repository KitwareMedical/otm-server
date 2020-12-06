<template>
  <v-data-table
    :loading="loading"
    item-key="id"
    :items="images"
    :headers="headers"
  />
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
      images: [],
      loading: true,
    };
  },
  computed: {
    headers() {
      return [
        {
          text: 'Name',
          value: 'name',
        },
        {
          text: 'Description',
          value: 'description',
        },
      ];
    },
  },
  async mounted() {
    // TODO pagination
    this.loading = true;
    const resp = await this.girderRest.get('images', { params: { dataset: this.datasetId }});
    this.images = resp.data.results;
    this.loading = false;
  }
};
</script>
