
import '@mdi/font/css/materialdesignicons.min.css';
import axios from 'axios';
import Vue from 'vue';
import Girder from '@girder/components';
import App from './App.vue';
import router from './router';
import vuetify from './vuetify';

Vue.use(Girder);

const girderRest = axios.create({
  baseURL: process.env.VUE_APP_API_ROOT,
});

new Vue({
  vuetify,
  router,
  render: (h) => h(App),
  provide: { girderRest, vuetify },
}).$mount('#app');
