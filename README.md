# Project is work in progress. Implementing the business case below for learning opportunity for Python.

## Bank X Application

Consider the following business case:

Bank X has defined a specification for a new Banking Application. In keeping up with the trends around the world, Bank X
wants to be able to allow both internal and external systems to connect with the new application. 

The Application must allow new customers to be onboarded and to obtain new accounts. 

Each customer with be provided with a Current and Savings account upon onboarding and will have their Savings Account 
credited with a joining bonus of R500.00. 

Customers should be able to move money between their accounts. Only the Current Account should be enabled to make payments to
other accounts. 

All payments made into the Savings Account will be credited with a 0.5% interest of the current balance.

All payments made from the customer’s account will be charged 0.05% of the transaction amount. 

The application must keep track of every transaction performed on the accounts and allow other systems to retrieve these. 

The system must send out notifications to the customer for every transaction event. 

Bank X also want to allow Bank Z to be able debit or credit the customer’s account for any transactions that were handled 
by Bank Z on behalf of Bank X. Bank Z should be able to send a single immediate transaction or a list of transactions 
which should be processed immediately. Bank Z should be able to send Bank X a list of transactions that they processed 
on behalf of Bank X at the end of the business day for reconciliation (Note: this is an offline process).
