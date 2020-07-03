<template>
  <div>
    <h2>Users</h2>
    <b-table
      :items="userTableData"
      :tbody-tr-class="rowClass"
      :fields="fields"
      stacked="md"
      hover
    ></b-table>
  </div>
</template>

<script>
  import axios from 'axios';

  export default {
    name: 'Users',

    data(){
      return {
        users: [],
        fields: [
          {
            key: 'username',
            label: 'Username',
          },
          {
            key: 'email',
            label: 'Email',
          },
          {
            key: 'status',
            label: 'Active',
          }
        ]
      }
    },

    computed: {
      userTableData(){
        return this.users.map(user => {
          return {
            username: user.username,
            email: user.email,
            status: user.active,
            _rowVariant: user.active ? 'success' : '',
          }
        })
      }
    },

    methods: {
    },

    mounted(){
      axios.get('users?full=true')
        .then(response => {
          this.users = response.data;
        })
    }
  };
</script>

<style scoped>

</style>
