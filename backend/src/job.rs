use std::collections::HashMap;
use std::pin::Pin;
use tokio::sync::watch;

#[derive(Clone)]
pub enum JobStatus {
    Pending,
    InProgress,
    Completed(String),
    Failed(String),
}


pub struct JobHandle {
    job_id: String,
    job_status: watch::Sender<HashMap<String, JobStatus>>,
}

impl JobHandle {
    pub fn set_status(&self, status: JobStatus) {
        self.job_status.send_modify(|s| {
            s.insert(self.job_id.clone(), status);
        });
    }

    pub fn get_id(&self) -> &str {
        &self.job_id
    }
}


pub struct JobPool {
    jobs_status: watch::Sender<HashMap<String, JobStatus>>,
}

pub type BoxFuture = Pin<Box<dyn Future<Output = ()> + Send>>;
pub type JobFn = Box<dyn FnOnce(JobHandle) -> BoxFuture + Send>;

impl JobPool {
    pub fn new() -> Self {
        let (tx, _) = watch::channel(HashMap::<String, JobStatus>::new());
        JobPool {
            jobs_status: tx,
        }
    }

    pub fn submit_job(&mut self, job: JobFn) -> String 
    {
        let job_id = uuid::Uuid::new_v4().to_string();
        let handle = JobHandle {
            job_id: job_id.clone(),
            job_status: self.jobs_status.clone(),
        };

        handle.set_status(JobStatus::Pending);
        tokio::spawn(job(handle));

        job_id
    }


    pub fn get_job_status(&self, job_id: &str) -> Option<JobStatus> {
        self.jobs_status.borrow().get(job_id).cloned()
    }

}

#[cfg(test)]
mod tests {
    use super::*;
    use tokio::time::Duration;

    #[tokio::test]
    async fn test_job_pool() {
        let mut job_pool = JobPool::new();
        let job_1 = job_pool.submit_job(Box::new(|handler: JobHandle| Box::pin(async move {
            handler.set_status(JobStatus::InProgress);
            tokio::time::sleep(Duration::from_secs(2)).await;
            handler.set_status(JobStatus::Completed("Job 1 completed".to_string()));
        })));

        let job_2 = job_pool.submit_job(Box::new(|handler:JobHandle| Box::pin(async move {
            tokio::time::sleep(Duration::from_secs(1)).await;
            handler.set_status(JobStatus::Completed("Job 2 completed".to_string()));
        })));

        let status_1 = job_pool.get_job_status(&job_1);
        let status_2 = job_pool.get_job_status(&job_2);

        assert!(matches!(status_1, Some(JobStatus::Pending)));
        assert!(matches!(status_2, Some(JobStatus::Pending)));
        tokio::time::sleep(Duration::from_millis(1500)).await;
        let status_1 = job_pool.get_job_status(&job_1).unwrap();
        let status_2 = job_pool.get_job_status(&job_2).unwrap();
        assert!(matches!(status_1, JobStatus::InProgress));
        assert!(matches!(status_2, JobStatus::Completed(_)));

        //wait for the jobs to complete
        println!("Waiting for jobs to complete");
        tokio::time::sleep(Duration::from_secs(3)).await;

        let status_1 = job_pool.get_job_status(&job_1).unwrap();
        let status_2 = job_pool.get_job_status(&job_2).unwrap();

        assert!(matches!(status_1, JobStatus::Completed(s) if s == "Job 1 completed"));
        assert!(matches!(status_2, JobStatus::Completed(s) if s == "Job 2 completed"));

    }
}