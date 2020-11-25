<template>
  <v-data-table
    :loading="loading"
    item-key="id"
    :items="datasets"
    :headers="headers"
  >
    <template #item.name="{ item }">
      <router-link :to="`upload/${item.id}`">
        {{ item.name }}
      </router-link>
    </template>
  </v-data-table>
</template>

<script>
export default {
  inject: ['girderRest'],
  data() {
    return {
      datasets: [],
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
    const resp = await this.girderRest.get('datasets');
    this.loading = false;
    this.datasets = resp.data.results;
  }
};
</script>
