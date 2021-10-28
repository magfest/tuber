<template>
    <div class="card">
        <h1>Welcome to Tuber!</h1>
        <p>This tuber deployment is configured for hotel management only.</p>
    </div>
</template>

<script>
export default {
  data () {
    return {
      products: null,
      lineData: {
        labels: ['January', 'February', 'March', 'April', 'May', 'June', 'July'],
        datasets: [
          {
            label: 'Revenue',
            data: [65, 59, 80, 81, 56, 55, 40],
            fill: false,
            backgroundColor: '#2f4860',
            borderColor: '#2f4860',
            tension: 0.4
          },
          {
            label: 'Sales',
            data: [28, 48, 40, 19, 86, 27, 90],
            fill: false,
            backgroundColor: '#00bb7e',
            borderColor: '#00bb7e',
            tension: 0.4
          }
        ]
      },
      items: [
        { label: 'Add New', icon: 'pi pi-fw pi-plus' },
        { label: 'Remove', icon: 'pi pi-fw pi-minus' }
      ]
    }
  },
  methods: {
    formatCurrency (value) {
      return value.toLocaleString('en-US', { style: 'currency', currency: 'USD' })
    }
  }
}
</script>
