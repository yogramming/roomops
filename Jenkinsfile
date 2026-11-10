pipeline {
    agent any

    options {
        timestamps()
        disableConcurrentBuilds()
        buildDiscarder(logRotator(numToKeepStr: '20'))
    }

    environment {
        CI_DB_CONTAINER = "roomops-ci-postgres-${BUILD_NUMBER}"
        CI_DB_NAME = "roomops_ci"
        CI_DB_USER = "roomops_ci"
        CI_DB_PASSWORD = "roomops_ci_test_password"
        PROMETHEUS_MULTIPROC_DIR = "${WORKSPACE}/.prometheus-multiproc"
        PIP_DISABLE_PIP_VERSION_CHECK = "1"
    }

    stages {
        stage('Checkout') {
            steps {
                checkout scm
            }
        }

        stage('Setup Python') {
            steps {
                sh '''
                    python3 --version

                    rm -rf "$PROMETHEUS_MULTIPROC_DIR"
                    mkdir -p "$PROMETHEUS_MULTIPROC_DIR"

                    python3 -m venv .ci-venv
                    .ci-venv/bin/python -m pip install -r requirements-dev.txt
                '''
            }
        }

        stage('Lint') {
            steps {
                sh '.ci-venv/bin/ruff check .'
            }
        }

        stage('Start PostgreSQL') {
            steps {
                script {
                    sh '''
                        docker run -d \
                            --name "$CI_DB_CONTAINER" \
                            -e POSTGRES_DB="$CI_DB_NAME" \
                            -e POSTGRES_USER="$CI_DB_USER" \
                            -e POSTGRES_PASSWORD="$CI_DB_PASSWORD" \
                            -p 127.0.0.1::5432 \
                            --health-cmd="pg_isready -U $CI_DB_USER -d $CI_DB_NAME" \
                            --health-interval=5s \
                            --health-timeout=3s \
                            --health-retries=10 \
                            postgres:17-alpine

                        for i in $(seq 1 30); do
                            STATUS=$(docker inspect \
                                --format='{{.State.Health.Status}}' \
                                "$CI_DB_CONTAINER")

                            if [ "$STATUS" = "healthy" ]; then
                                echo "PostgreSQL is ready."
                                exit 0
                            fi

                            echo "Waiting for PostgreSQL: $STATUS"
                            sleep 2
                        done

                        echo "PostgreSQL failed to become healthy."
                        docker logs "$CI_DB_CONTAINER"
                        exit 1
                    '''

                    env.CI_DB_PORT = sh(
                        script: '''
                            docker inspect \
                                --format='{{(index (index .NetworkSettings.Ports "5432/tcp") 0).HostPort}}' \
                                "$CI_DB_CONTAINER"
                        ''',
                        returnStdout: true
                    ).trim()

                    echo "PostgreSQL host port: ${env.CI_DB_PORT}"
                }
            }
        }

        stage('Database Migrations & Tests') {
            steps {
                withEnv([
                    "DATABASE_URL=postgresql+psycopg://${env.CI_DB_USER}:${env.CI_DB_PASSWORD}@127.0.0.1:${env.CI_DB_PORT}/${env.CI_DB_NAME}",
                    "TEST_DATABASE_URL=postgresql+psycopg://${env.CI_DB_USER}:${env.CI_DB_PASSWORD}@127.0.0.1:${env.CI_DB_PORT}/${env.CI_DB_NAME}"
                ]) {
                    sh '''
                        .ci-venv/bin/flask --app 'app:create_app()' db upgrade
                        .ci-venv/bin/python -m pytest -v
                    '''
                }
            }
        }

        stage('Build Docker Image') {
            steps {
                script {
                    env.IMAGE_TAG = sh(
                        script: 'git rev-parse --short=12 HEAD',
                        returnStdout: true
                    ).trim()
                }

                sh '''
                    docker build --pull \
                        -t "roomops:${IMAGE_TAG}" .

                    docker image inspect "roomops:${IMAGE_TAG}" \
                        --format='Image ID: {{.Id}}'
                '''
            }
        }

        stage('Trivy Security Scan') {
            steps {
                sh '''
                    trivy image \
                        --scanners vuln \
                        --skip-files "**/pip/_vendor/bom.cdx.json" \
                        --severity HIGH,CRITICAL \
                        --ignore-unfixed \
                        --exit-code 1 \
                        --no-progress \
                        "roomops:${IMAGE_TAG}"
                '''
            }
        }

        stage('Publish to Docker Hub') {
            steps {
                withCredentials([
                    usernamePassword(
                        credentialsId: 'dockerhub-credentials',
                        usernameVariable: 'DOCKERHUB_USER',
                        passwordVariable: 'DOCKERHUB_TOKEN'
                    )
                ]) {
                    sh '''
                        set +x

                        export DOCKER_CONFIG=$(mktemp -d)
                        trap 'docker logout >/dev/null 2>&1 || true; rm -rf "$DOCKER_CONFIG"' EXIT

                        IMAGE_NAME="$DOCKERHUB_USER/roomops"

                        printf '%s' "$DOCKERHUB_TOKEN" | \
                            docker login \
                                --username "$DOCKERHUB_USER" \
                                --password-stdin

                        docker tag "roomops:${IMAGE_TAG}" "${IMAGE_NAME}:${IMAGE_TAG}"
                        docker tag "roomops:${IMAGE_TAG}" "${IMAGE_NAME}:latest"

                        docker push "${IMAGE_NAME}:${IMAGE_TAG}"
                        docker push "${IMAGE_NAME}:latest"

                        echo "Successfully published ${IMAGE_NAME}:${IMAGE_TAG}"
                        echo "Successfully published ${IMAGE_NAME}:latest"
                    '''
                }
            }
        }
    }

    post {
        always {
            sh '''
                docker rm -f "$CI_DB_CONTAINER" 2>/dev/null || true
                rm -rf .ci-venv "$PROMETHEUS_MULTIPROC_DIR"
            '''
        }

        success {
            echo 'RoomOps CI pipeline completed successfully.'
        }

        failure {
            echo 'RoomOps CI pipeline failed. Check the stage logs.'
        }
    }
}

