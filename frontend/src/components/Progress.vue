<template>
    <div>
        <Accordion v-if="Object.keys(jobs).length > 0">
            <AccordionTab :header="job.name + ' - ' + job.status" v-for="job in jobs">
                <ProgressBar :value="Math.round(job.amount * 100)" :mode="job.definite ? 'determinate' : 'indeterminate'"></ProgressBar>
                <pre>{{ job.messages }}</pre>
            </AccordionTab>
        </Accordion>
    </div>
</template>

<script>
export default {
    name: 'Progress',
    data () {
        return {
            jobs: {}
        }
    },
    methods: {
        update (job, progress) {
            console.log("Updating job", job, progress)
            this.jobs[job] = progress
        },
        stop_job (job) {
            console.log("Stopping job", job)
            delete this.jobs[job]
        }
    }
}
</script>
