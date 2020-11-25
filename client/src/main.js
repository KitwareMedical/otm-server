
import axios from 'axios';
import Vue from 'vue';
import Girder, { vuetify } from '@girder/components/src';
import App from './App.vue';
import router from './router';

Vue.use(Girder);
const girderRest = axios.create({
  baseURL: process.env.VUE_APP_API_ROOT,
});

new Vue({
  vuetify,
  router,
  render: (h) => h(App),
  provide: { girderRest },
}).$mount('#app');
