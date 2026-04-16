#!/bin/bash

BASE_URL="http://13.126.197.136:30007"

POST_URL="$BASE_URL/bank/canara/transfer"
ORDER_URL="$BASE_URL/swiggy/order"
PAYMENT_URL="$BASE_URL/phonepe/payment"
REALTIME_URL="$BASE_URL/swiggy/realtime"
METRIC_URL="$BASE_URL/demo/user-metric"

for batch in {1..10}; do
  for i in {1..100}; do
    (
      # POST request
      post_status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X POST "$POST_URL/$i/1" \
        -H "accept: application/json" \
        -d '')

      # ORDER
      order_status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X GET "$ORDER_URL/$i/1" \
        -H "accept: application/json")

      # PAYMENT
      payment_id=$(( (i % 100) + 1 ))
      payment_status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X GET "$PAYMENT_URL/$payment_id" \
        -H "accept: application/json")

      # REALTIME
      realtime_status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X GET "$REALTIME_URL/$i/1/1" \
        -H "accept: application/json")

      # METRIC
      metric_status=$(curl -s -o /dev/null -w "%{http_code}" \
        -X GET "$METRIC_URL/$i" \
        -H "accept: application/json")

      echo "User $i → POST:$post_status ORDER:$order_status PAYMENT:$payment_status REALTIME:$realtime_status METRIC:$metric_status"
    ) &
  done
  wait
done

echo "Done"